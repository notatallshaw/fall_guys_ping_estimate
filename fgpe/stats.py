# Standard Library
import csv
from pathlib import Path
from datetime import datetime
from os.path import expandvars
from collections import defaultdict
from statistics import mean, median, quantiles, StatisticsError
from typing import DefaultDict, Optional

# Local Libraries
from .log_reader import ConnectionDetails


class Stats:
    """
    Keep Stats of connection details and then write to file
    """
    def __init__(self, avg_size: int = 10):
        self.avg_size = avg_size
        self.recent_pings: DefaultDict[ConnectionDetails, list[int]] = defaultdict(list)
        self.ping_count: DefaultDict[ConnectionDetails, int] = defaultdict(int)
        self.ping_start_time: dict[ConnectionDetails, datetime] = {}
        self.current_connection_details: Optional[ConnectionDetails] = None

        # Define stats file, check file and directory exists
        self.stats_csv_path = Path(expandvars(r'%APPDATA%\fgpe\stats.csv'))
        self.stats_csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.stats_csv_path.exists():
            self.stats_csv_path.write_text('Start Time,End Time,IP Address,Port,Count,Min,Max,Median,Mean,75th,90th\n')


    def add(self, connection_details: ConnectionDetails, time: int) -> None:
        self.current_connection_details = connection_details
        self.ping_count[connection_details] += 1
        self.recent_pings[connection_details].append(time)
        if connection_details not in self.ping_start_time:
            self.ping_start_time[connection_details] = datetime.now()

    def stats_string(self, connection_details: ConnectionDetails) -> str:
        current_ping = self.recent_pings[connection_details][-1]
        max_ping = max(self.recent_pings[connection_details])
        min_ping = min(self.recent_pings[connection_details])
        rolling_average_ping = float(mean(self.recent_pings[connection_details][-self.avg_size:]))
        return (f'Ping={current_ping}ms, '
                f'Min={min_ping}ms, '
                f'Max={max_ping}ms, '
                f'Avg({min([len(self.recent_pings[connection_details]), self.avg_size])})={rolling_average_ping:.1f}ms')
    
    def end_session(self, connection_details: Optional[ConnectionDetails]) -> None:
        if connection_details is None or connection_details.ip == '0.0.0.0':
            return

        now = datetime.now()
        min_ping = min(self.recent_pings[connection_details])
        max_ping = max(self.recent_pings[connection_details])
        median_ping = median(self.recent_pings[connection_details])
        mean_ping = mean(self.recent_pings[connection_details])
        try:
            percentile_75 = float(quantiles(self.recent_pings[connection_details], method='inclusive')[-1])
        except StatisticsError:
            percentile_75 = ''

        try:
            percentile_90 = float(quantiles(self.recent_pings[connection_details], n=10, method='inclusive')[-1])
        except StatisticsError:
            percentile_90 = ''

        with open(self.stats_csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.ping_start_time[connection_details].strftime('%Y-%m-%d %H:%M:%S'),
                now.strftime('%Y-%m-%d %H:%M:%S'),
                connection_details.ip,
                connection_details.port,
                self.ping_count[connection_details],
                min_ping,
                max_ping,
                median_ping,
                mean_ping,
                percentile_75,
                percentile_90
            ])

        del self.recent_pings[connection_details]
        del self.ping_count[connection_details]
        del self.ping_start_time[connection_details]