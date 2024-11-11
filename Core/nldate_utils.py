import re
import datetime as dt

nldate = {'jan': '01',
          'feb': '02',
          'mrt': '03',
          'apr': '04',
          'mei': '05',
          'jun': '06',
          'jul': '07',
          'aug': '08',
          'sep': '09',
          'okt': '10',
          'nov': '11',
          "dec": '12'}

match = {1: 'Januari',
         2: 'Februari',
         3: 'Maart',
         4: 'April',
         5: 'Mei',
         6: 'Juni',
         7: 'Juli',
         8: 'Augustus',
         9: 'September',
         10: 'Oktober',
         11: 'November',
         12: 'December'}


def filter_date(line):
    pattern = r'(\d{1,2} (%s) \d{4})' % ('|'.join(nldate))
    return re.findall(pattern, line)


def replace_months(date):
    """This function replaces the names of months in the strings"""
    for i, j in nldate.items():
        date = date.replace(i, j)
    return date


def format_date(date):
    """This function formats a date in the nlwiki format. The returned date only contains information on the day,
    month, and year the request was passed """
    assert isinstance(date, str), "Please pass a string as the argument of format_date!"
    return dt.datetime.strptime(replace_months(date),
                                '%d %m %Y')  # this is the object that can actually do the job for us


def get_date_for_lines(lines):
    """This function will return the most recent contribution date that corresponds with a given request."""
    if isinstance(lines, str):  # Single line is passed, no need to invert or loop here!
        try:
            date_temp = filter_date(lines)[0][0]
            return format_date(date_temp)
        except IndexError:
            return None  # Explicitly return None to avoid syntax errors
    elif isinstance(lines, (list, tuple)):  # Mulitple lines of text are passed at once
        for k in lines[::-1]:  # Run the inverse
            try:
                date_temp = filter_date(k)[0][0]  # Get the date on that line (using Regex)
                return format_date(date_temp)  # Convert the found date into an actual DateTime
            except IndexError:  # It's easier to ask for forgiveness, as this sin can be forgiven easily.
                return None
