"""
An auxiliary method for processing date-related properties for the archiver

@author: Daniuu

Functions implemented:
    1)
    2)
"""

import pytz
import datetime as dt
import nldate

timezone = pytz.timezone('Europe/Amsterdam')

current_time = dt.datetime.now(timezone)

year = current_time.year

month = current_time.month

day = current_time.day


# Some special stuff, has to do with the REGBLOK archives
def determine_regblok_archive_number(date=None):  # delay = 0 removed for efficiency
    # Some start data (interesting as a reference)
    start = 48
    startdate = dt.datetime(2023, 1, 1, tzinfo=timezone)
    if date is None:
        date = dt.datetime.now(timezone)

    # date -= dt.timedelta(days=delay)  # Became obsolete, because the request submission day is used as reference

    # Calculate the difference between the current date and the reference
    diff_year = date.year - startdate.year
    second_year_half = (date.month >= 7)*1  # New archive started every six months
    return str(start + 2*diff_year + second_year_half)


# WP:TERUG uses some very weird archive convention :(
def obscure_archive_number(date=None):
    # Returns a or b (depending on the time of the year)
    if date.month < 7:
        return 'a'
    return 'b'


# Format archive for any given date
def format_archive_for_date(date, archive_with_parameters):
    # Note: method is usually called with date = date at which request got filed
    # 20240722 - implement failsafe for None type
    # This feature will be used for pages that don't use sections
    if archive_with_parameters is None:
        return None
    temp = archive_with_parameters.replace('$YEAR', str(date.year))
    temp = temp.replace('$MONTH', str(date.month))
    temp = temp.replace('$NAMEMONTH', nldate.match[date.month])
    temp = temp.replace('$DAY', str(date.day))
    if '$REGBLOKNR' in temp:
        temp = temp.replace('$REGBLOKNR', determine_regblok_archive_number(date))
    if '$TERUG' in temp:
        temp = temp.replace('$TERUG', obscure_archive_number(date))
    return temp
