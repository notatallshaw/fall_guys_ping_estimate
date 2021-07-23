# Standard Library
import os
import sys
import time
from typing import Optional

# Third Party Modules
import psutil

# Local Modules
from .stats import Stats
from .overlay import Overlay
from .pinger import Pinger, PingConnect
from .log_reader import LogReader, ServerState, ConnectionDetails


class Events:
    """
    This the main logic that is called by the GUIs event loop
    """
    def __init__(self):
        self.reader = LogReader()
        self.stats = Stats()
        self.current_connection: Optional[ConnectionDetails] = None

    def close(self, _) -> None:
        self.stats.end_session(self.current_connection)
        sys.exit()

    def update_text(self) -> str:
        # Check if Fall Guys is Running
        log_age = time.time() - os.path.getmtime(self.reader.log_location)
        if log_age > 3_600:
            return 'Fall Guys Game is not Running'
        
        if log_age > 5:
            # No update log so check if process is running
            for process in psutil.process_iter():
                if process.name() == 'FallGuys_client_game.exe':
                    break
            else:
                self.stats.end_session(self.current_connection)
                self.current_connection = None
                return 'Fall Guys Game is not Running'

        # Check if connected to Fall Guys Server
        status, connection =  self.reader.get_connection_details()
        if status != ServerState.CONNECTED:
            self.stats.end_session(self.current_connection)
            self.current_connection = None
            return f'Not Connected to Fall Guys Server'
        
        # Set Current Connection
        self.current_connection = connection

        # Check if can ping IP
        pinger = Pinger(connection.ip)
        status, ping_time = pinger.get_ping_time()
        if status != PingConnect.CONNECTED:
            return f'Could not reach Fall Guys IP: {connection}'

        # Update Stats and Report
        self.stats.add(connection, ping_time)
        return f'IP={pinger.ip_address}, {self.stats.stats_string(connection)}'


def main():
    events = Events()
    overlay = Overlay(events.close, events.update_text)
    overlay.run()


if __name__ == '__main__':
    main()
