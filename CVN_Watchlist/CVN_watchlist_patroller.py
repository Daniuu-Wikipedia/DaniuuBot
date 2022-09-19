# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 11:54:30 2022

@author: Daniuu

A dedicated bot designed to patrol https://nl.wikipedia.org/wiki/Wikipedia:Controlelijst_vandalismebestrijding

This file contains the code that is used to patrol the page.
The functionality for the time zones is listed in two other files.
"""

import Core_CVN as core
import datetime as dt
import re 

def format_date(date):
    "Converts a datetime.datetime instance into an ISO-8601 format (supported by the Wikimedia API)"
    if not isinstance(date, dt.datetime):
        raise TypeError('Please pass a valid datetime.datetime object')
    return date.isoformat() #L = we are using local time of the wiki

class Part:
    """
    The class processes one _day part_
    Arguments: start- and end-time. A dedicated script will be developed to handle time zone changes.
    Times should be passed as datetime.datetime in utc.
    """
    def __init__(self, start, end):
        assert start <= end, "The order of the arguments of a datepart got inverted!"
        self.start, self.end = start, end
        self.nredits = -1 #Not checked at this point
        self.get_unpatrolled_edits()
    
    def get_unpatrolled_edits(self):
        pay = {'action':'query',
               'list':'recentchanges',
               'rcdir':'newer',
               'rcstart':format_date(self.start),
               'rcend':format_date(self.end),
               'rcprop':'title',
               'rclimit':3, #At this point, we only want to know whether or not there are unpatrolled edits.
               'rcshow':'anon|unpatrolled'}
    
    def __eq__(self, other):
        return self.start == other.start and self.end == other.end
    
    def __lt__(self, other):
        return self.start < other.start

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
           'rcstart':format_date(dt.datetime(2022, 9, 6, 0, 0, 0)),
           'rcend':format_date(dt.datetime(2022, 9, 6, 6, 0, 0, 0)), #Staat in lokale tijd for some reason
           'rcprop':'title|user|timestamp',
           'rclimit':50,
           'rcshow':'anon|unpatrolled'}
    repl = (bot.get(pay))
    print(repl)
    print(len(repl['query']['recentchanges']))
    