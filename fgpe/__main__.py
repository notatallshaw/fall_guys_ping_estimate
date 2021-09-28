# Standard Library
import os
import sys
import csv
import time
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from tempfile import TemporaryDirectory

# Third Party Modules
import psutil
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Local Modules
from .stats import Stats
from .overlay import Overlay
from .pinger import Pinger, PingConnect
from .locations import LocationLookup, UNKNOWN_LOCATION
from .log_reader import LogReader, ServerState, ConnectionDetails

# Globals
IP_URL = 'https://raw.githubusercontent.com/notatallshaw/fall_guys_ping_estimate/main/fgpe/data/Fall_Guys_IP_Networks.csv'
API_URL = 'https://api.github.com/repos/notatallshaw/fall_guys_ping_estimate/commits?path=fgpe%2Fdata%2FFall_Guys_IP_Networks.csv'


class Events:
    """
    This the main logic that is called by the GUIs event loop
    """
    def __init__(self):
        self.reader = LogReader()
        self.stats = Stats()
        self.locations = LocationLookup()
        self.current_connection: Optional[ConnectionDetails] = None
        self.has_first_run = False

    def close(self, _) -> None:
        self.stats.end_session(self.current_connection)
        sys.exit()

    def first_run(self) -> str:
        # Check if recently updated
        if self.locations.download_csv_file_path.exists():
            # After successful commit wait 1 hour before checking again
            if time.time() - self.locations.download_csv_file_path.stat().st_mtime < 24 * 60:
                return 'IP Addresses already updated recently'

        with requests.Session() as session:
            retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            
            # Get last commit time for comparison
            api_response = session.get(API_URL)
            api_response.raise_for_status()
            last_commit_timestamp = datetime.strptime(api_response.json()[0]["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

            # Return is already up to date
            if self.locations.download_csv_file_path.exists():
                file_timestamp = self.locations.download_csv_file_path.stat().st_mtime
                if file_timestamp >= last_commit_timestamp:
                    return "IP Addresses are already up to date"

            # Get new file
            response = session.get(IP_URL)
            response.raise_for_status()
            with TemporaryDirectory() as temp_dir:
                temp_file = Path(temp_dir) / self.locations.download_csv_file_path.name
                temp_file.write_bytes(response.content)
                os.utime(temp_file, (last_commit_timestamp, last_commit_timestamp))
                shutil.move(temp_file, self.locations.download_csv_file_path)
            self.locations.clear_ip_network_lookup_cache()

        # Clear existing Unknown IP addresses
        if self.locations.unknown_ip_path.exists():
            updated = False
            with TemporaryDirectory() as temp_dir:
                temp_file = Path(temp_dir) / self.locations.unknown_ip_path.name
                with open(self.locations.unknown_ip_path) as f_in, open(temp_file, 'w', newline='') as f_out:
                    reader = csv.DictReader(f_in)
                    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    for row in reader:
                        if self.locations.lookup(row["IP Address"], record_unknown=False) is UNKNOWN_LOCATION:
                            writer.writerow(row)
                        else:
                            updated = True
                if updated:
                    shutil.move(temp_file, self.locations.unknown_ip_path)
        return 'Downloaded new IP addresses'
        

    def update_text(self) -> tuple[int, str]:
        """
        Return tuple of milliseconds till next update and string message to display
        """
        # Do a first run
        if not self.has_first_run:
            self.has_first_run = True
            try:
                return (1_000, self.first_run())
            except Exception as e:
                return (5_000, f'Failed to download new IP addresses: {str(e)}')

        # Check if Fall Guys is Running
        log_age = time.time() - os.path.getmtime(self.reader.log_location)
        if log_age > 30 * 60:
            return (1_000, 'Fall Guys Game is not Running')
        
        if log_age > 5:
            # No update log so check if process is running
            for process in psutil.process_iter():
                if process.name() == 'FallGuys_client_game.exe':
                    break
            else:
                self.stats.end_session(self.current_connection)
                self.current_connection = None
                return (10_000, 'Fall Guys Game is not Running')

        # Check if connected to Fall Guys Server
        status, connection =  self.reader.get_connection_details()
        if status != ServerState.CONNECTED:
            self.stats.end_session(self.current_connection)
            self.current_connection = None
            return (1_000, 'Not Connected to Fall Guys Server')
        
        # Set Current Connection
        self.current_connection = connection

        # Check if can ping IP
        pinger = Pinger(connection.ip)
        status, ping_time = pinger.get_ping_time()
        if status != PingConnect.CONNECTED:
            return (1_000, f'Could not reach Fall Guys IP: {connection.ip}')

        # Update Stats, lookup location, and report
        self.stats.add(connection, ping_time)
        location = self.locations.lookup(pinger.ip_address)
        if location == UNKNOWN_LOCATION:
            return (5_000, f'IP={pinger.ip_address}, {self.stats.stats_string(connection)}')
        return (5_000, f'Region={location.region}, Location={location.location}, {self.stats.stats_string(connection)}')


def main():
    events = Events()
    overlay = Overlay(
        events.close,
        'Checking for IP address updates...',
        500,
        events.update_text
        )
    overlay.run()


if __name__ == '__main__':
    main()
