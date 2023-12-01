import datetime
from exif import Image
import os
import re
import sys
import time

DRY_RUN = "DRY_RUN" in os.environ

def to_unix(date):
    unix_ts = time.mktime(date.timetuple())
    return unix_ts

def parse_YYYYMMDDHHMMSS(filepath):
    expression = (
        "(?P<year>20[0-9]{2}).?"
        "(?P<month>[0-9]{2}).?"
        "(?P<day>[0-9]{2}).?"
        "(?P<hour>[0-9]{2}).?"
        "(?P<min>[0-9]{2}).?"
        "(?P<sec>[0-9]{2})"
    )
    pattern = re.search(expression, filepath)
    if not pattern:
        return None
    year     = int(pattern.group('year'))
    month    = int(pattern.group('month'))
    day  = int(pattern.group('day'))
    hour     = int(pattern.group('hour'))
    minute = int(pattern.group('min'))
    second = int(pattern.group('sec'))
    try:
        date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    except ValueError:
        return None
    return date

def parse_YYYYMMDD(filepath):
    expression = (
        "(?P<year>2[0-9]{3}).?"
        "(?P<month>[0-9]{2}).?"
        "(?P<day>[0-9]{2})"
    )
    pattern = re.search(expression, filepath)
    if not pattern:
        return None
    year     = int(pattern.group('year'))
    month    = int(pattern.group('month'))
    day  = int(pattern.group('day'))
    try:
        date = datetime.datetime(year=year, month=month, day=day)
    except ValueError:
        return None
    return date

def date_exif(fullpath):
    if os.path.getsize(fullpath) > 25_000_000:
        return None
    try:
        with open(fullpath, 'rb') as image_file:
            my_image = Image(image_file)
        if my_image.has_exif and hasattr(my_image, "datetime"):
            date_raw = my_image.datetime
            date = parse_YYYYMMDDHHMMSS(date_raw)
            return date
        return None
    except Exception as e:
        return None

def find_date(fullpath):
    date = date_exif(fullpath)\
        or parse_YYYYMMDDHHMMSS(fullpath)\
        or parse_YYYYMMDD(fullpath)
    return date

if __name__ == "__main__":
    dir_to_rename = sys.argv[1]
    for root, _, files in os.walk(dir_to_rename):
        for file in files:
            fullpath = f"{root}/{file}"
            date = find_date(fullpath)

            if date:
                print(f"found this date for {fullpath}: {date}")
            else:
                print(f"can't parse date for {file}")

            if not DRY_RUN and date:
                unix_ts = to_unix(date)
                os.utime(fullpath, (unix_ts, unix_ts))
