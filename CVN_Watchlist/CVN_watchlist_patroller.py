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
        if to_UTC(self.end) <= dt.datetime.utcnow() <= start + dt.timedelta(days=30): 
            #Don't mark a slot as completed when it is not yet completed.
            #Don't mark a slot when it expired
            #There is no use in making an API query for a slot that is not yet finished
            self.get_unpatrolled_edits() #Switch off to make tests faster
            #pass
    
    def get_unpatrolled_edits(self):
        pay = {'action':'query',
               'list':'recentchanges',
               'rcdir':'newer', #This parameter must be conserved if you don't want to break the bot
               'rcstart':format_date(self.start),
               'rcend':format_date(self.end),
               'rcprop':'title',
               'rclimit':2, #At this point, we only want to know whether or not there are unpatrolled edits.
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
        timestring = f'*{wikidate(self.start, False)} - {wikidate(self.end, False)}:'
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
    month_to_text = {1:'januari',
                     2:'februari',
                     3:'maart',
                     4:'april',
                     5:'mei',
                     6:'juni',
                     7:'juli',
                     8:'augustus',
                     9:'september',
                     10:'oktober',
                     11:'november',
                     12:'december'} #To convert the months into a proper title
    month_regex = f'({"|".join(month_to_text.values())})'
        
    def __init__(self, text):
        #Parameters to set: date of the request + the list containing the requests
        self.slots, self.date = [], None #A blank list to store all the uncompleted slots in
        for i in text.split('\n'):
            if i.startswith('*'):
                if Part.template in i:
                    s, e = i[:-2].split('|')[1:] #Start and end dates of each timeslot
                    sd = dt.datetime.strptime(s, r'%d-%m-%Y %H:%M')
                    try:
                        ed = dt.datetime.strptime(e, r'%d-%m-%Y %H:%M')
                    except ValueError: #Weird convention (24:00) - workaround
                        ed = dt.datetime.strptime(e.replace('24:00', '23:00'), r'%d-%m-%Y %H:%M')
                        ed += dt.timedelta(hours=1) #Add one hour post-factum
                    self.slots.append(Part(sd, ed)) #Write the effective part
                    if self.date is None:
                        self.date = dt.datetime(sd.year, sd.month, sd.day,
                                                0, 0, 0)
                else:
                    self.slots.append(i.strip())       
    
    #Function needed to regenerate the page that contains all days
    def __str__(self):
        "Produces the date-section that is re-inserted into the page"
        #if self: #All edits from this day were patrolled
        #    return '' #Blank this section
        #Write the full string for the section
        title = f'=== Anoniemen {self.date.day} {Day.month_to_text[self.date.month]} ==='
        sl = '\n'.join((str(i) for i in self.slots)) #Strings of the slots
        fd = r'<small>{{%s|%s|%s|label=Controleer of alles van deze dag gedaan is}}</small>'%\
            (Part.template, wikidate(self.date, True), wikidate(self.tomorrow, True))
        return f'{title}\n{sl}\n\n{fd}\n'
    
    def __bool__(self):
        "Indicates whether all edits of this day were patrolled"
        return all(self.slots) or self.date is None #if the date is None, the slots should have been handled
    
    #Functions to support sorting these objects
    def __lt__(self, other):
        return self.date < other.date
    
    def __eq__(self, other):
        return (self.date.day, self.date.month, self.date.year) == (other.date.day, other.date.month, other.date.year)
    
    #Hash
    def __hash__(self):
        return self.date.isoformat().__hash__()
    
    def __repr__(self):
        return f'{self.date.day}-{self.date.month}'
    
    @property
    def tomorrow(self):
        if self.date is None:
            return self.date.utcnow() + dt.timedelta(days=1)
        return self.date + dt.timedelta(days=1)
    
    @property 
    def expired(self):
        return self.date + dt.timedelta(days=31) < dt.datetime.utcnow() #31 days to have 1 day as a buffer
    
    @staticmethod
    def new_day(date):
        "This method generates a section for the next day"
        if not isinstance(date, dt.datetime):
            raise TypeError(f'Please pass a datetime to the new_day function, not a {type(date)}-object.')
        date = date.replace(hour=0, minute=0, second=0, microsecond=0) #Reset   
        #Generate the different timeslots
        slots = [Part(date, date + dt.timedelta(hours=6)),
                 Part(date + dt.timedelta(hours=6), date + dt.timedelta(hours=10.5))] #A list of dates
        slots += [Part(date + dt.timedelta(hours=10.5 + i*1.5), date + dt.timedelta(hours=10.5 + (i + 1)*1.5)) for i in range(9)]
        out = Day()
        out.slots = slots #Use the backdoor to enter these
        return out
    
    @staticmethod
    def gen_tomorrow():
        return Day.new_day(dt.datetime.utcnow() + dt.timedelta(days=1))
        
class Page:
    "All function to manipulate the contents of the request page"
    api = core.NlBot()
    preheader = 'Algemeen'
    postheader = 'Artikelen of IP-adressen met meeste ongemarkeerde (ongecontroleerde?) anonieme edits (kan snel vervallen door controle)'
    
    def __init__(self, title="Wikipedia:Controlelijst vandalismebestrijding"):
        self._title = title
        
        #Load page content & TOC (and load them into their respective variables)
        pay = {'action':'parse',
               'page':self._title,
               'prop':'sections|wikitext'}
        raw = Page.api.get(pay)['parse']
        wikitext = raw['wikitext']['*'] #Full contents of the page
        self.toc = raw['sections'] #Store the TOC
        del raw #Remove memory-consuming auxiliary variable
        self._splits = sorted(((i['byteoffset'], int(i['index'])) for i in self.toc if i['line'] in {Page.preheader,
                                                                       Page.postheader}))
        #All text before and after the section that is relevant for us
        self._pre, self._post = f'{wikitext[:self._splits[0][0]]}== {Page.preheader} ==\n', wikitext[self._splits[1][0]:]
        
        #Find the sections that contain the different patrolling sections
        rel_sec = self.toc[self._splits[0][1]:self._splits[1][1] + 1] #+1 in final to make slicing easier
        self.dates = []
        for i, j in zip(rel_sec[:-1], rel_sec[1:]):
            if i['line'].startswith('Anoniemen'):
                self.dates.append(Day(wikitext[i['byteoffset']:j['byteoffset']]))
        del wikitext, rel_sec #Delete memory-consuming auxiliary variables
    
    def __str__(self):
        date_processed = "\n".join((str(i) for i in self.dates))
        return f'{self._pre}{date_processed}{self._post}'
    
    def update(self):
        "Refreshes the page"
        payload = {'action':'edit',
                   'title':'Gebruiker:Daniuu/Kladblok',
                   'text':str(self),
                   'summary':'Testing a script',
                   'notminor':True,
                   'nocreate':True}
        print(Page.api.post(payload))
        
    def clean_old(self):
        "This method purges the old pages"
        oldies = [i for i in self.dates if i.expired]
        for i in oldies:
            self.dates.remove(i)
        print(self.dates)
    
    def make_new(self):
        "Creates a new section for the upcoming day"
        new = Day.gen_tomorrow()
        if new not in self.dates:
            self.dates.append(new)
    
        
    
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

a = Page('Gebruiker:Daniuu/Kladblok')

a.clean_old()