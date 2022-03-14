"""
Handles looking up IPs via Third Party API
Caches results for a given amount of time
not to overwhelm third party API

Third party APIs for looking up IP addresses
Can often have very limiting terms of service

The best one I have found so far that works
for the usage of this tool is:
    ip-api.com
"""
# Standard library
import csv
import time
import shutil
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

# Third Party Libraries
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Logger
logger = logging.getLogger(__name__)

# Globals
IP_QUERY = 'http://ip-api.com/json/{query}?fields=66846719'
OLDEST_FRESHNESS = 7.0 * 24.0 * 60.0 * 60.0  # 7 Days


class Lookup:
    def __init__(self, cache_dir):
        # Set up caches
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        self.ip_cache_path = cache_dir / 'ip_cache.csv'
        self.ip_cache = self.get_cache(self.ip_cache_path, 'query')

        self.as_cache_path = cache_dir / 'as_cache.csv'
        self.as_cache = self.get_cache(self.as_cache_path, 'asnumber')

        # Setup HTTP session
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def get_cache(
            self,
            file_path: Path,
            index_field: str
            ) -> dict[str, dict[str, str]]:
        if not file_path.exists():
            return {}

        cache = {}
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cache[row[index_field]] = row

        return cache

    def save_cache(
            self,
            file_path: Path,
            cache: dict[str, dict[str, str]]
            ) -> None:
        if not cache:
            return

        # Write cache to a tempory location,
        # then move to correct location
        rows = iter(cache.values())
        with TemporaryDirectory() as temp:
            temp_file_path = Path(temp) / file_path.name
            with open(temp_file_path, 'w', newline='') as f:
                first_row = next(rows)
                writer = csv.DictWriter(f, fieldnames=first_row.keys())
                writer.writeheader()
                writer.writerow(first_row)
                writer.writerows(rows)

            try:
                shutil.move(temp_file_path, file_path)
            except Exception:
                logger.exception(f'Failed to write cache file {str(file_path)!r}:')

    def is_ip_info_fresh(self, ip: str) -> bool:
        """
        If as info is fresh and the information associated with it
        hasn't changed since last IP lookup then we do not need to do
        another lookup. This is because IP addresses are associated
        with as blocks, for more info read about BGP routing
        """
        if ip not in self.ip_cache:
            return False

        ip_info = self.ip_cache[ip]
        as_number = ip_info['asnumber']
        as_info = self.as_cache.get(as_number)
        if as_info is None:
            return False

        if float(ip_info['local_freshness']) < float(as_info['local_oldest']):
            return False

        if float(as_info['local_freshness']) < time.time() - OLDEST_FRESHNESS:
            return False

        return True

    def lookup(self, ip) -> dict:
        if self.is_ip_info_fresh(ip):
            return self.ip_cache[ip]

        # Live IP query
        query = IP_QUERY.format(query=ip)
        api_response = self.session.get(query, timeout=5).json()

        # Add API response to IP cache
        now = str(time.time())
        api_response['local_freshness'] = now
        as_number = api_response['as'].split()[0]
        api_response['asnumber'] = as_number
        self.ip_cache[ip] = api_response

        # Check if IP response provided new as info
        api_org = api_response['org']
        api_continent = api_response['continent']
        api_country = api_response['country']
        api_region = api_response['region']
        api_city = api_response['city']

        # Check if as info needs updating
        update_as_info = False
        as_info = self.as_cache.get(as_number)
        if as_info is None:
            update_as_info = True
        else:
            as_org = as_info['org']
            as_continent = as_info['continent']
            as_country = as_info['country']
            as_region = as_info['region']
            as_city = as_info['city']
            if ((api_org, api_continent, api_country, api_region, api_city) !=
               (as_org, as_continent, as_country, as_region, as_city)):
                update_as_info = True

        if update_as_info:
            self.as_cache[as_number] = {
                'asnumber': as_number,
                'org': api_org,
                'continent': api_continent,
                'country': api_country,
                'region': api_region,
                'city': api_city,
                'local_freshness': now,
                'local_oldest': now
            }
        else:
            self.as_cache[as_number]['local_freshness'] = now

        self.save_cache(self.ip_cache_path, self.ip_cache)
        self.save_cache(self.as_cache_path, self.as_cache)

        return api_response
