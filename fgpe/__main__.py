# Standard Library
import os
import time

# Third Party Modules
import psutil

# Local Modules
from .overlay import Overlay
from .pinger import Pinger, Stats, PingConnect
from .log_reader import LogReader, ServerState


class Events:
    """
    This the main logic that is called by the GUIs event loop
    """
    def __init__(self):
        self.reader = LogReader()
        self.stats = Stats()

    def __call__(self) -> str:
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
                return 'Fall Guys Game is not Running'

        # Check if connected to Fall Guys Server
        status, ip_port =  self.reader.get_ip()
        if status != ServerState.CONNECTED:
            self.stats = Stats()
            return f'Not Connected to Fall Guys Server'

        # Check if can ping IP
        pinger = Pinger(ip_port)
        status, ping_time = pinger.get_ping_time()
        if status != PingConnect.CONNECTED:
            self.stats = Stats()
            return f'Could not reach Fall Guys IP: {ip_port}'

        # Update Stats and Report
        self.stats.add(ping_time)
        return f'IP={pinger.ip_address}, {self.stats.stats_string()}'


def main():
    events = Events()
    overlay = Overlay(events)
    overlay.run()


if __name__ == '__main__':
    main()
