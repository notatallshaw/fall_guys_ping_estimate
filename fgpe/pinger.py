# Standard Library
import subprocess
from enum import Enum
from typing import Optional


class PingConnect(Enum):
    CONNECTED = 1
    NOT_CONNECTED = 2


class Pinger:
    """
    Calls a subprocess to run the ping command and then parses the results

    Unforutnatly this can't in pure Python without admin privilages
    As a normal process requires admin for an ICMP request (ping) 
    """
    def __init__(self, ip_address: str):
        if ':' in ip_address:
            self.ip_address, self.port = ip_address.split(':')
        else:
            self.ip_address = ip_address
            self.port = None

    def get_ping_time(self) -> tuple[PingConnect, Optional[int]]:
        response = subprocess.run(
            ['ping', '-n', '1', '-w', '1000', self.ip_address],
            stdin=subprocess.PIPE,  # Required for PyInstaller --noconsole
            capture_output=True,
            encoding='ascii',
            creationflags=subprocess.CREATE_NO_WINDOW  # Required for noflickering in exe
            )
        if response.returncode != 0:
            return PingConnect.NOT_CONNECTED, None

        for line in response.stdout.splitlines():
            if 'Reply from' in line:
                time_equals = line.strip().split()[4]
                time_ms = time_equals.split('=')[1]
                time = int(time_ms[:-2])
                break
        else:
            return PingConnect.NOT_CONNECTED, None

        return PingConnect.CONNECTED, time
