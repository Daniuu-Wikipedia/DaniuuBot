# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 11:54:30 2022

@author: Daniuu
"""

import Core_CVN as core
import datetime as dt
import re 

def format_date(date):
    "Converts a datetime.datetime instance into an ISO-8601 format (supported by the Wikimedia API)"
    if not isinstance(date, dt.datetime):
        raise TypeError('Please pass a valid datetime.datetime object')
    return f'+{date.isoformat()}L' #L = we are using local time of the wiki

#Process one single day
class Day:
    """
    This class processes one day worth of requests. 
    It reads the different parts of the day that remain unchecked and processes them.
    Arguments to be passed upon construction:
        * Text: the text that contains all of the parts of the day
    """
    def __init__(self, text):
        #Parameters to set: date of the request + the list containing the requests
        pass 
    
    #Function needed to regenerate the page that contains all days
    def __str__(self):
        "Produces the date-section that is re-inserted into the page"
        if self: #All edits from this day were patrolled
            return '' #Blank this section
        pass
    
    def __bool__(self):
        "Indicates whether all edits of this day were patrolled"
        pass
    
    #Functions to support sorting these objects
    def __lt__(self, other):
        return self.date < other.date
    
    def __eq__(self, other):
        return self.date == other.date
    
    #Hash
    def __hash__(self):
        return self.date.isoformat().__hash__()
    
#Some testcode
if __name__ == '__main__':
    print('Running check')
    bot = core.NlBot()
    print(format_date(dt.datetime(2022, 9, 6, 0, 0)))
    pay = {'action':'query',
           'list':'recentchanges',
           'rcdir':'newer',
           'rcstart':format_date(dt.datetime(2022, 9, 6, 0, 0)),
           'rcend':format_date(dt.datetime(2022, 9, 6, 6, 0, 0)),
           'rcprop':'title|user|timestamp',
           'rclimit':50,
           'rctype':'anon|unpatrolled'}
    print(bot.get(pay))
    