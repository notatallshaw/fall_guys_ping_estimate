# Standaard Libraries
from typing import NamedTuple

# Local Libraries
from fgpe.ip_lookup import Lookup


class FallGuysLocation(NamedTuple):
    region: str
    location: str
    provider: str


class LocationLookup:
    """
    Take the information provided by the IP lookup
    to display useful information like what Fall Guys
    region is it.
    """
    def __init__(self, data_directory):
        self.ip_lookup = Lookup(data_directory)

    def lookup(self, ip: str) -> FallGuysLocation:
        ip_info = self.ip_lookup.lookup(ip)

        return FallGuysLocation(
            region=ip_info['continent'],
            location=ip_info['city'],
            provider=ip_info['org'],
        )
