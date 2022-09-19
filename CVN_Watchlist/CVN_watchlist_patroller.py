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
from Timezones import offset

def to_UTC(date):
    "Converts a given date in Amsterdam time to UTC"
    if not isinstance(date, dt.datetime):
        raise TypeError('Only valid dateTIME-instances can be processed by the to_UTC function!')
    return date + offset(date) #offset from the separate script

def format_date(date):
    """Converts a datetime.datetime instance into an ISO-8601 format (supported by the Wikimedia API).
    The function automatically converts a given LOCAL time into a UTC-format. 
    This function allows the code to use local times everywhere.
    """
    if not isinstance(date, dt.datetime):
        raise TypeError('Please pass a valid datetime.datetime object')
    return f'{to_UTC(date).isoformat()}Z' #L = we are using local time of the wiki - Z = UTC time

def wikidate(d, showday):
    """
    This function converts a give day into a format that can be used on the wiki (human-readable)

    Parameters
    ----------
    d : dt.datetime
        The date that is printed to the wiki.
    showday : boolean
        Determines whether or not the date is printed.
    """
    timestring = f'{d.hour:02d}:{d.minute:02d}'
    if not isinstance(showday, bool):
        raise TypeError('Showday must be a boolean, not %s'%showday)
    if showday is True:
        return f'{d.day:02d}-{d.month:02d}-{d.year:02d} {timestring}'
    return timestring
            
class Part:
    """
    The class processes one _day part_
    Arguments: start- and end-time. A dedicated script will be developed to handle time zone changes.
    Times should be passed as datetime.datetime in utc.
    """
    api = core.NlBot() #Use one bot for all queries
    template = 'Gebruiker:Krinkle/cvlijst2/rclink' #The template that is used to link to the revisions to be patrolled
    
    def __init__(self, start, end):
        assert start <= end, "The order of the arguments of a datepart got inverted!"
        self.start, self.end = start, end
        self.nredits = -1 #Not checked at this point
        self.get_unpatrolled_edits()
    
    def get_unpatrolled_edits(self):
        pay = {'action':'query',
               'list':'recentchanges',
               'rcdir':'newer', #This parameter must be conserved if you don't want to break the bot
               'rcstart':format_date(self.start),
               'rcend':format_date(self.end),
               'rcprop':'title',
               'rclimit':10, #At this point, we only want to know whether or not there are unpatrolled edits.
               'rcshow':'anon|unpatrolled'}
        self.nredits = len(Part.api.get(pay)['query']['recentchanges'])
    
    def __eq__(self, other):
        return self.start == other.start and self.end == other.end
    
    def __lt__(self, other):
        return self.start < other.start
    
    def __len__(self):
        return self.nredits
    
    def __bool__(self):
        return self.nredits == 0 #Check if there are still edits that should be patrolled
    
    def __str__(self):
        "This function converts a slot into a format that can be interpreted by humans"
        #General prefix (always mentioned: the times)
        timestring = f'{wikidate(self.start, False)} - {wikidate(self.end, False)}:'
        if self: #Self bool(self) is True, all edits were patrolled
            return "%s {{d|'''Gecontroleerd'''}} - ~~~~"%timestring
        #There are still edits that need patrolling
        tempar = "{{%s|%s|%s}}"%(Part.template, wikidate(self.start, True), wikidate(self.end, True))
        return f'{timestring} {tempar}'
        
        
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
    bot = core.NlBot()
    pay = {'action':'query',
           'list':'recentchanges',
           'rcdir':'newer',
           'rcstart':format_date(dt.datetime(2022, 9, 6, 0, 0, 0)),
           'rcend':format_date(dt.datetime(2022, 9, 6, 6, 0, 0, 0)), #Staat in lokale tijd for some reason
           'rcprop':'title|user|timestamp',
           'rclimit':50,
           'rcshow':'anon|unpatrolled'}

#Other testcode
k = dt.datetime(2022, 11, 1, 9, 0)

pt = Part(dt.datetime(2022, 9, 6, 0, 0, 0), dt.datetime(2022, 9, 6, 6, 0, 0))
print(pt)

real = r"00:00 - 06:00: {{Gebruiker:Krinkle/cvlijst2/rclink|06-09-2022 00:00|06-09-2022 06:00}}"
print(str(pt) == real)
