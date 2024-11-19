import time

class Service:
    def read_timestamp_date(self, string):
        if not string:
            return ''

        try:
            timestamp = int(string)
            if timestamp < 0:
                return '11.11.2011'
            return time.strftime('%d.%m.%Y', time.gmtime(timestamp))
        except (ValueError, OSError):
            return ''