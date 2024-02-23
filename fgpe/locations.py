# Standaard Libraries
import csv
from pathlib import Path
import importlib.resources
from functools import cache
from typing import NamedTuple
from datetime import datetime
from os.path import expandvars, exists
from ipaddress import ip_address, ip_network, _BaseNetwork
import geoip2.database

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
        self._backup_csv_file: Path = importlib.resources.files('fgpe') / 'data' / 'Fall_Guys_IP_Networks.csv'
        self.download_csv_file_path = Path(expandvars(r'%APPDATA%\fgpe\Fall_Guys_IP_Networks.csv'))
        self._ip_network_lookup = None

        geoip_path = Path(expandvars(r'%APPDATA%\fgpe\GeoLite2-City.mmdb'))
        self._use_geoip = geoip_path.exists()
        if self._use_geoip:
            self._geoip_reader = geoip2.database.Reader(geoip_path)

        # Check unknown IP address CSV exists
        self.unknown_ip_path = Path(expandvars(r'%APPDATA%\fgpe\unknown_ip_addresses.csv'))
        self.unknown_ip_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.unknown_ip_path.exists():
            self.unknown_ip_path.write_text('Time,IP Address\n')
    
    def __del__(self):
        if self._use_geoip:
            self._geoip_reader.close()

    @property
    def csv_file_path(self) -> Path:
        if self.download_csv_file_path.exists():
            return self.download_csv_file_path
        return self._backup_csv_file

    @property
    def ip_network_lookup(self) -> dict[_BaseNetwork, FallGuysLocation]:
        if self._ip_network_lookup is not None:
            return self._ip_network_lookup

        ip_network_lookup = {}
        with open(self.csv_file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ip_network_lookup[ip_network(row['IP Network'])] = \
                    FallGuysLocation(row['Fall Guys Region'], row['Location'], row['Provider'])

        self._ip_network_lookup = ip_network_lookup
        return self._ip_network_lookup

    def clear_ip_network_lookup_cache(self) -> None:
        self._ip_network_lookup = None

    @cache
    def lookup(self, ip_str: str, record_unknown: bool = True) -> FallGuysLocation:
        ip_addr = ip_address(ip_str)
        if self._use_geoip:
            geoip_response = self._geoip_reader.city(ip_addr)
            return FallGuysLocation(geoip_response.country.name, geoip_response.city.name, 'Unknown')

        for network, location in self.ip_network_lookup.items():
            if ip_addr in network:
                return location

        if not record_unknown:
            return UNKNOWN_LOCATION

        with open(self.unknown_ip_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ip_str,
            ])

        return UNKNOWN_LOCATION
        
