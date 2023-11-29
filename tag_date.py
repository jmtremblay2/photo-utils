import datetime
import time
import re
import os
import sys


def parse_signal_file(filepath):
    expression = (
        "(?P<year>2[0-9]{3}).?"
        "(?P<month>[0-9]{2}).?"
        "(?P<day>[0-9]{2}).?"
        "(?P<hour>[0-9]{2}).?"
        "(?P<min>[0-9]{2}).?"
        "(?P<sec>[0-9]{2})"
    )
    pattern = re.search(expression, filepath)
    if not pattern:
        return None, None
    year     = int(pattern.group('year'))
    month    = int(pattern.group('month'))
    day  = int(pattern.group('day'))
    hour     = int(pattern.group('hour'))
    minute = int(pattern.group('min'))
    second = int(pattern.group('sec'))
    try:
        date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    except ValueError:
        return None, None
    unix_ts = time.mktime(date.timetuple())
    return date, unix_ts

def parse_YYYY_MM_DD(filepath):
    expression = (
        "(?P<year>2[0-9]{3}).?"
        "(?P<month>[0-9]{2}).?"
        "(?P<day>[0-9]{2})"
    )
    pattern = re.search(expression, filepath)
    if not pattern:
        return None, None
    year     = int(pattern.group('year'))
    month    = int(pattern.group('month'))
    day  = int(pattern.group('day'))
    try:
        date = datetime.datetime(year=year, month=month, day=day)
    except ValueError:
        return None, None
    unix_ts = time.mktime(date.timetuple())
    return date, unix_ts

date_fns = [
    parse_signal_file,
    parse_YYYY_MM_DD
]

if __name__ == "__main__":
    dir_to_rename = sys.argv[1]
    dry_run = len(sys.argv) > 2 and sys.argv[2] == "dry-run"
    for root, _, files in os.walk(dir_to_rename):
        for file in files:
            for fn in date_fns:
                date, unix_ts = fn(file)
                if date is not None:
                    break
            if date is None:
                print(f"can't parse date for {file}")
                continue
            fullpath = f"{root}/{file}"
            if dry_run:
                print(f"{fullpath}:   --   {date}  --  {unix_ts}")
            else: 
                os.utime(fullpath, (unix_ts, unix_ts))            
    
