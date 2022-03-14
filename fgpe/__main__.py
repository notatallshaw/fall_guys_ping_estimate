# Standard Library
import os
import sys
import csv
import time
import shutil
import logging
from pathlib import Path
from typing import Optional
from os.path import expandvars
from datetime import datetime, timezone
from tempfile import TemporaryDirectory

# Third Party Modules
import psutil
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # type: ignore

# Local Modules
from .stats import Stats
from .pinger import Pinger, PingConnect
from .overlay import Overlay, GracefulExit
from .locations import LocationLookup, UNKNOWN_LOCATION
from .log_reader import LogReader, ServerState, ConnectionDetails

# Logger
logger = logging.getLogger(__name__)

# Globals
IP_URL = 'https://raw.githubusercontent.com/notatallshaw/fall_guys_ping_estimate/main/fgpe/data/Fall_Guys_IP_Networks.csv'
API_URL = 'https://api.github.com/repos/notatallshaw/fall_guys_ping_estimate/commits?path=fgpe%2Fdata%2FFall_Guys_IP_Networks.csv'
DATA_DIRECTORY = expandvars(r'%APPDATA%\fgpe')


class Events:
    """
    This the main logic that is called by the GUIs event loop
    """
    def __init__(self, exit_after_n_updates=None):
        self.reader = LogReader()
        self.stats = Stats()
        self.locations = LocationLookup()
        self.current_connection: Optional[ConnectionDetails] = None
        self.has_first_run = False
        self.exit_on_n_updates = exit_after_n_updates
        self.n_updates = 0

    def close(self, _) -> None:
        self.stats.end_session(self.current_connection)
        sys.exit()

    def _check_if_for_updated_ips(self) -> None:
        with requests.Session() as session:
            retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))

            # Get last commit time for comparison
            api_response = session.get(API_URL, timeout=10)
            api_response.raise_for_status()
            last_commit_timestamp = datetime.strptime(api_response.json()[0]["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

            # Return is already up to date
            if self.locations.download_csv_file_path.exists():
                file_timestamp = self.locations.download_csv_file_path.stat().st_mtime
                if file_timestamp >= last_commit_timestamp:
                    return

            # Get new file
            response = session.get(IP_URL, timeout=10)
            if response.status_code != 200:
                return

            with TemporaryDirectory() as temp_dir:
                temp_file = Path(temp_dir) / self.locations.download_csv_file_path.name
                temp_file.write_bytes(response.content)
                os.utime(temp_file, (last_commit_timestamp, last_commit_timestamp))
                shutil.move(temp_file, self.locations.download_csv_file_path)
            self.locations.clear_ip_network_lookup_cache()

    def _clear_old_ips(self) -> None:
        # Clear existing Unknown IP addresses
        if self.locations.unknown_ip_path.exists():
            updated = False
            with TemporaryDirectory() as temp_dir:
                temp_file = Path(temp_dir) / self.locations.unknown_ip_path.name
                with open(self.locations.unknown_ip_path) as f_in, open(temp_file, 'w', newline='') as f_out:
                    reader = csv.DictReader(f_in)
                    if reader.fieldnames is None:
                        return
                    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    for row in reader:
                        if self.locations.lookup(row["IP Address"], record_unknown=False) is UNKNOWN_LOCATION:
                            writer.writerow(row)
                        else:
                            updated = True
                if updated:
                    shutil.move(temp_file, self.locations.unknown_ip_path)

    def first_run(self) -> str:
        # Check if recently updated
        if self.locations.download_csv_file_path.exists():
            # After successful commit wait 1 hour before checking again
            if time.time() - self.locations.download_csv_file_path.stat().st_mtime < 24 * 60:
                return 'IP Addresses already updated recently'

        try:
            result = self._check_if_for_updated_ips()
        except Exception:
            logger.exception('Unexpected exception checking for IPs')
            return 'Error checking for new IP Addresses'

        if result is None:
            return "IP Addresses are already up to date"

        try:
            self._clear_old_ips()
        except Exception:
            logger.exception('Unexpected exception clearing old IPs')
            return 'Error clearing old IP Addresses'

        return 'Downloaded new IP addresses'

    def _clear_connection(self) -> None:
        self.stats.end_session(self.current_connection)
        self.current_connection = None

    def _check_process(self) -> bool:
        for process in psutil.process_iter():
            if process.name() == 'FallGuys_client_game.exe':
                return True
        return False

    def update_text(self) -> tuple[int, str]:
        """
        Return tuple of milliseconds till next update and string message to display
        """
        # Check if need to exit
        if self.exit_on_n_updates is not None:
            self.n_updates += 1
            if self.exit_on_n_updates >= self.n_updates:
                raise GracefulExit(f'Exiting on {self.n_updates} updates')

        # Do a first run
        if not self.has_first_run:
            self.has_first_run = True
            return 1_000, self.first_run()

        # Check if Fall Guys is Running
        log_age = time.time() - os.path.getmtime(self.reader.log_location)
        if log_age > 30 * 60:
            self._clear_connection()
            return (1_000, 'Fall Guys Game is not Running')

        if log_age > 10:
            try:
                process_result = self._check_process()
            except Exception:
                logger.exception('Unexpected exception checking for process')
                return (500, 'Error checking Fall Guys Status')

            if not process_result:
                self._clear_connection()
                return (10_000, 'Fall Guys Game is not Running')

        # Check if connected to Fall Guys Server
        status, connection =  self.reader.get_connection_details()
        if status != ServerState.CONNECTED:
            self._clear_connection()
            return (1_000, 'Not Connected to Fall Guys Server')

        # Set Current Connection
        self.current_connection = connection

        # Check if can ping IP
        pinger = Pinger(connection.ip)
        status, ping_time = pinger.get_ping_time()
        if status != PingConnect.CONNECTED or ping_time is None:
            return (1_000, f'Could not reach Fall Guys IP: {connection.ip}')

        # Update Stats, lookup location, and report
        self.stats.add(connection, ping_time)
        location = self.locations.lookup(pinger.ip_address)
        if location == UNKNOWN_LOCATION:
            return (5_000, f'IP={pinger.ip_address}, {self.stats.stats_string(connection)}')
        return (5_000, f'Region={location.region}, Location={location.location}, {self.stats.stats_string(connection)}')


def run_overlay(exit_after_n_updates=None):
    events = Events(exit_after_n_updates)
    overlay = Overlay(
        events.close,
        'Checking for IP address updates...',
        500,
        events.update_text
        )
    overlay.run()


def set_up_logs():
    log_directory = Path(DATA_DIRECTORY)
    log_directory.mkdir(parents=True, exist_ok=True)
    error_log = log_directory / 'errors.log'
    logging.basicConfig(
        filename=str(error_log),
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )


def main():
    set_up_logs()
    run_overlay()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logger.exception('FGPE ended with unexpected exception:')
