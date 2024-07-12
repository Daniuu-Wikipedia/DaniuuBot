"""
An auxiliary method for processing date-related properties for the archiver

@author: Daniuu

Functions implemented:
    1)
    2)
"""

import pytz
import datetime as dt

timezone = pytz.timezone('Europe/Amsterdam')

current_time = dt.datetime.now(timezone)

year = current_time.year

month = current_time.month

day = current_time.day


# Some special stuff, has to do with the REGBLOK archives
def determine_regblok_archive_number(date=None, delay=0):
    # Some start data (interesting as a reference)
    start = 48
    startdate = dt.datetime(2023, 1, 1, tzinfo=timezone)
    if date is None:
        date = dt.datetime.now(timezone)

    date -= dt.timedelta(days=delay)

    # Calculate the difference between the current date and the reference
    diff_year = date.year - startdate.year
    second_year_half = (date.month >= 7)*1  # New archive started every six months
    return start + 2*diff_year + second_year_half
