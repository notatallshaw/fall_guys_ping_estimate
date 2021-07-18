import os
import time
from enum import Enum
from typing import Optional

class ServerState(Enum):
    CONNECTED = 1
    NOT_CONNECTED = 2
    GAME_STARTING = 3

class FileReader:
    """
    Reads Fall Guys Logs to get current connected IP address
    """
    def __init__(self):
        self.position = 0
        self.current_ip_address = None
        self.current_server_state = ServerState.NOT_CONNECTED
        self.game_start_time = None
        self.log_mtime = None
        self.log_location = os.path.expandvars(r'%USERPROFILE%\AppData\LocalLow\Mediatonic\FallGuys_client\Player.log')

        # Check file exists
        if not os.path.exists(self.log_location):
            raise ValueError(f'No log file at: {self.log_location}')
    
    def file_updated(self):
        new_log_mtime = os.path.getmtime(self.log_location)
        updated = self.log_mtime == new_log_mtime
        self.log_mtime = new_log_mtime
        return updated

    def file_changed(self):
        with open(self.log_location) as f:
            for line in f:
                if '[GlobalGameStateClient].PreStart called at' in line:
                    new_game_start_time = line.split()[-2]
                    break
            else: # If never broken
                return None
        
        changed = self.game_start_time == new_game_start_time
        self.game_start_time = new_game_start_time
        return changed
    
    def get_ip(self) -> tuple[ServerState, Optional[str]]:
        ip_address = self.current_ip_address

        if not self.file_updated():
            changed = self.file_changed()
            if changed is None:
                self.current_ip_address = None
                self.current_server_state = ServerState.GAME_STARTING
                return self.current_server_state, self.current_ip_address
            elif changed:
                self.position = 0
            
            with open(self.log_location) as f:
                f.seek(self.position)
                for line in f:
                    if '[FG_UnityInternetNetworkManager] Client Disconnected from Server' in line:
                        ip_address = None
                    if "[StateConnectToGame] We're connected to the server!" in line:
                        ip_address = line.split()[-1]

                # Record last position and IP address so we don't read file too many times
                self.position = f.tell()
                self.current_ip_address = ip_address
        
        if ip_address is None:
            self.current_server_state = ServerState.NOT_CONNECTED
        else:
            self.current_server_state = ServerState.CONNECTED
        
        return self.current_server_state, self.current_ip_address
