# Standard Library
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional
from os.path import expandvars

# Third Party Modules
import psutil

# Local Modules
from .stats import Stats
from .pinger import Pinger, PingConnect
from .overlay import Overlay, GracefulExit
from .locations import LocationLookup
from .log_reader import LogReader, ServerState, ConnectionDetails

# Logger
logger = logging.getLogger(__name__)

# Globals
DATA_DIRECTORY = expandvars(r'%APPDATA%\fgpe')


class Events:
    """
    This the main logic that is called by the GUIs event loop
    """
    def __init__(self, exit_after_n_updates=None):
        self.reader = LogReader()
        self.stats = Stats()
        self.locations = LocationLookup(DATA_DIRECTORY)
        self.current_connection: Optional[ConnectionDetails] = None
        self.exit_on_n_updates = exit_after_n_updates
        self.n_updates = 0

    def close(self, _) -> None:
        self.stats.end_session(self.current_connection)
        sys.exit()

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
        Return tuple of milliseconds till next update and string
        message to display
        """
        # Check if need to exit
        if self.exit_on_n_updates is not None:
            self.n_updates += 1
            if self.exit_on_n_updates >= self.n_updates:
                raise GracefulExit(f'Exiting on {self.n_updates} updates')

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
        status, connection = self.reader.get_connection_details()
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
        return (
            5_000,
            f'Region={location.region}, '
            f'Location={location.location}, '
            f'{self.stats.stats_string(connection)}'
            )


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
