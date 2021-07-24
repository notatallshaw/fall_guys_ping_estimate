# Standaard Libraries
import csv
from pathlib import Path
import importlib.resources
from functools import cache
from typing import NamedTuple
from datetime import datetime
from os.path import expandvars
from ipaddress import ip_address, ip_network, _BaseNetwork


class FallGuysLocation(NamedTuple):
    region: str
    location: str
    provider: str


UNKNOWN_LOCATION = FallGuysLocation('Unknown', 'Unknown', 'Unknown')


class LocationLookup:
    """
    Based on manually derived data look up the location of the Fall Guys server
    """
    def __init__(self):
        """
        Prepopulate the IP Network Lookups
        """
        # importlib.resources.files returns a file type
        csv_file: Path = importlib.resources.files('fgpe') / 'data' / 'Fall_Guys_IP_Networks.csv'
        
        self.ip_network_lookup: dict[_BaseNetwork, FallGuysLocation] = {}
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.ip_network_lookup[ip_network(row['IP Network'])] = \
                    FallGuysLocation(row['Fall Guys Region'], row['Location'], row['Provider'])

        # Check unknown IP address CSV exists
        self.unknown_ip_path = Path(expandvars(r'%APPDATA%\fgpe\unknown_ip_addresses.csv'))
        self.unknown_ip_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.unknown_ip_path.exists():
            self.unknown_ip_path.write_text('Time,IP Address\n')

    @cache    
    def lookup(self, ip_str: str) -> FallGuysLocation:
        ip_addr = ip_address(ip_str)
        for network, location in self.ip_network_lookup.items():
            if ip_addr in network:
                return location

        with open(self.unknown_ip_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ip_str,
            ])

        return UNKNOWN_LOCATION
        
