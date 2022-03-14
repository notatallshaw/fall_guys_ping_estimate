import os
from enum import Enum
from dataclasses import dataclass


class ServerState(Enum):
    CONNECTED = 1
    NOT_CONNECTED = 2


@dataclass(frozen=True)
class ConnectionDetails:
    ip: str
    port: str


class LogReader:
    """
    Reads Fall Guys Logs to get current connected IP address
    """
    def __init__(self):
        self.position = 0
        self.current_ip = '0.0.0.0'
        self.current_port = '0'
        self.current_server_state = ServerState.NOT_CONNECTED
        self.prev_log_mtime = None
        self.prev_log_location = os.path.expandvars(r'%USERPROFILE%\AppData\LocalLow\Mediatonic\FallGuys_client\Player-prev.log')
        self.log_mtime = None
        self.log_location = os.path.expandvars(r'%USERPROFILE%\AppData\LocalLow\Mediatonic\FallGuys_client\Player.log')

    def log_updated(self) -> bool:
        if not os.path.exists(self.log_location):
            return False

        new_log_mtime = os.path.getmtime(self.log_location)
        updated = not (self.log_mtime == new_log_mtime)
        self.log_mtime = new_log_mtime
        return updated

    def log_changed(self) -> bool:
        if not os.path.exists(self.prev_log_location):
            return False

        new_prev_log_mtime = os.path.getmtime(self.prev_log_location)        
        changed = self.prev_log_mtime == new_prev_log_mtime
        self.prev_log_mtime = new_prev_log_mtime
        return changed

    def _update_ip_from_log_file(self) -> None:
        if not os.path.exists(self.log_location):
            return

        ip_address = self.current_ip
        port = self.current_port

        with open(self.log_location, errors='ignore') as f:
            f.seek(self.position)
            for line in f:
                if '[FG_UnityInternetNetworkManager] FG_NetworkManager shutdown completed!' in line:
                    ip_address = '0.0.0.0'
                    port = '0'
                elif "[StateConnectToGame] We're connected to the server!" in line:
                    ip_address, port = line.split()[-1].split(':')

            # Record last position and IP address so we don't read file too many times
            self.position = f.tell()
            self.current_ip = ip_address
            self.current_port = port

    def get_connection_details(self) -> tuple[ServerState, ConnectionDetails]:
        if self.log_updated():
            if self.log_changed():
                self.position = 0
            self._update_ip_from_log_file()

        if self.current_ip == '0.0.0.0':
            self.current_server_state = ServerState.NOT_CONNECTED
        else:
            self.current_server_state = ServerState.CONNECTED

        return self.current_server_state, ConnectionDetails(self.current_ip, self.current_port)
