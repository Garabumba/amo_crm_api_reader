import time
from datetime import datetime, timedelta

class Service:
    def read_timestamp_date(self, string):
        if not string:
            return ''

        try:
            timestamp = int(string)
            if timestamp < 0:
                return '2011-11-11'
            #return time.strftime('%Y-%m-%d', time.gmtime(timestamp))
            date_with_offset = datetime.fromtimestamp(timestamp) + timedelta(hours=3)
            #date_with_offset = datetime.fromtimestamp(datetime.utcfromtimestamp(timestamp) + timedelta(hours=3)
            return date_with_offset.strftime('%Y-%m-%d')
        except (ValueError, OSError):
            return ''