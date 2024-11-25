import time

class Service:
    def read_timestamp_date(self, string):
        if not string:
            return ''

        try:
            timestamp = int(string)
            if timestamp < 0:
                return '2011-11-11'
            return time.strftime('%Y-%m-%d', time.gmtime(timestamp))
        except (ValueError, OSError):
            return ''