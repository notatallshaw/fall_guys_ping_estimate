import os
import time
from enum import Enum
from typing import Optional

class ServerState(Enum):
    CONNECTED = 1
    NOT_CONNECTED = 2

class LogReader:
    """
    Reads Fall Guys Logs to get current connected IP address
    """
    def __init__(self):
        self.position = 0
        self.current_ip_address = None
        self.current_server_state = ServerState.NOT_CONNECTED
        self.prev_log_mtime = None
        self.prev_log_location = os.path.expandvars(r'%USERPROFILE%\AppData\LocalLow\Mediatonic\FallGuys_client\Player-prev.log')
        self.log_mtime = None
        self.log_location = os.path.expandvars(r'%USERPROFILE%\AppData\LocalLow\Mediatonic\FallGuys_client\Player.log')

        # Check file exists
        if not os.path.exists(self.log_location):
            raise ValueError(f'No log file at: {self.log_location}')
    
    def log_updated(self) -> bool:
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
        ip_address = self.current_ip_address
        with open(self.log_location) as f:
            f.seek(self.position)
            for line in f:
                if '[FG_UnityInternetNetworkManager] FG_NetworkManager shutdown completed!' in line:
                    ip_address = None
                elif "[StateConnectToGame] We're connected to the server!" in line:
                    ip_address = line.split()[-1]

            # Record last position and IP address so we don't read file too many times
            self.position = f.tell()
            self.current_ip_address = ip_address

    
    def get_ip(self) -> tuple[ServerState, Optional[str]]:
        if self.log_updated():
            if self.log_changed():
                self.position = 0
            self._update_ip_from_log_file()
        
        if self.current_ip_address is None:
            self.current_server_state = ServerState.NOT_CONNECTED
        else:
            self.current_server_state = ServerState.CONNECTED
        
        return self.current_server_state, self.current_ip_address
