# -*- coding: utf-8 -*-
"""
Created on Sun Jun 20 12:21:36 2021

@author: Daniuu

This script is designed to automatically patrol the Dutch Wikipedia IPBLOK-request page
Please note: this script is still in an experimental phase, 
"""

import Core as c
import datetime as dt
import re


class IPBLOK(c.Page):
    "This class contains the main content for the page related operations"
    def __init__(self):
        super().__init__('Wikipedia:Verzoekpagina voor moderatoren/IPBlok')
        self.regex = None #Store the default regex pattern here
        self.prepare_regex()
    
    def separate(self):
        return super().separate('Nieuwe verzoeken', 'Afgehandelde verzoeken')
    
    def prepare_regex(self):
        "Prepare the regex-pattern for future searches"
        #Prepare the regex pattern
        ip4 = r'(\d{1,3}\.){3}\d{1,3}' #Regex pattern used to detect ip4-adresses (and ranges)
        ip6 = r'([\dABCDEF]{1,4}:){4,7}([\dABCDEF:]{1,4})+?' #Regex pattern used to detect ip4-adresses (and ranges)
        templates = ('lg', 'lgipcw', 'lgcw', 'linkgebruiker', 'Link IP-gebruiker cross-wiki', 'lgx')
        regex_template = r'\{\{(%s)\|'%('|'.join(templates)) #A pattern that makes handling the templates easier
        self.regex = '(%s(%s|%s))'%(regex_template, ip4, ip6)
        return self.regex
    
    def check_line(self, line):
        "This function checks whether an IP is on the line, and returns those"
        if self.regex is None:
            self.prepare_regex() #The regex has not yet been initialized properly
        k = re.findall(self.regex, line)
        if not k:
            return None #Returns None, indicating that the list of matches is empty
        if isinstance(k[0], tuple):
            k = list(k[0]) #Overwrite this with a proper list of matches
        return [Request(i) for i in k if ('{{' in i and '|' in i and (i.count('.') == 3 or i.count(':') >= 4))] #Only return the matches that are real calls to the template
    
    def check_all(self):
        for i in self._queue[1:]:
            print(self.check_line(i))
        
class Request(c.GenReq):
    bot = c.TestBot() #We are now testing
    now = dt.datetime.utcnow() #Store the current time to check whether 
    
    def __init__(self, ip):
        super().__init__(ip, (str,))
        self.blocks, self.gb = [], []
        self.main = None #This is where we will store the block that is primarily affecting the person here
            
    def process(self, origin):
        if '|' not in origin:
            return origin.strip().upper().strip()
        return origin.split('|')[1].strip()
    
    def get_blocks(self):
        "This function will check whether the user was blocked or not"
        dic = {'action':'query',
               'list':'blocks|globalblocks',
               'bkip':self.target,
               'bgip':self.target,
               'bklimit':500,
               'bglimit':500,
               'bkprop':'user|by|timestamp|expiry',
               'bgprop':'address|by|timestamp|expiry'}
        output = Request.bot.get(dic)['query']
        self.blocks, self.gb = output['blocks'], output['globalblocks']
        self.process_blocks() #Automatically call this function too
    
    def process_blocks(self):
        "This function will ensure the blocks are properly formatted"
        #Begin with the global blocks
        for i in self.gb:
            i['global'] = True #Just adding this for further use in the API
            i['user'] = i['address'] #Something to make it compatible with the normal blocks
            start, end = i['timestamp'], i['expiry'] #Some date formatting
            if not isinstance(start, dt.datetime):
                i['timestamp'] = self.convert_api_date(start)
            if not isinstance(end, dt.datetime):
                i['expiry'] = self.convert_api_date(end)
                end = i['expiry']
                
        for i in self.blocks:
            i['global'] = False #Someone is only locally blocked, just add False in the global header
            start, end = i['timestamp'], i['expiry'] #Some date formatting
            if not isinstance(start, dt.datetime):
                i['timestamp'] = self.convert_api_date(start)
            if not isinstance(end, dt.datetime):
                i['expiry'] = self.convert_api_date(end)
                end = i['expiry']
    
    def check_blocked(self, delay=0): #For the test phase
        "This function will check whether a given IP is blocked. A 10 minute delay prior to flagging is used"
        self.get_blocks() #First, get the blocks from the API
        self.blocks.sort(key=lambda i:i['timestamp'], reverse=True) #Sort, most recent blocks first
        too_old = Request.now - dt.timedelta(hours=1)
        for i in self.blocks:
            if too_old <= i['timestamp'] + dt.timedelta(minutes=delay) <= Request.now: #This gives the blocking sysop the time to place a block
                if i['expiry'] > Request.now: #Verify that the block did not yet expire
                    self.main = i
                    return self.main
        
        #Now check the global blocks
        self.gb.sort(key=lambda i:i['timestamp'], reverse=True)
        for i in self.gb:
            if i['timestamp'] + dt.timedelta(minutes=delay) <= Request.now: #This gives the blocking sysop the time to place a block
                if i['expiry'] > Request.now: #Verify that the block did not yet expire
                    self.main = i
                    return self.main
    
    def __bool__(self):
        "This function will convert the entire function into a boolean"
        return self.main is not None
    
    def get_and_check_block(self):
        "This function will combine some of the functions above"
        self.get_blocks()
        self.check_blocked()
    
    def get_name(self):
        "This method will return the name of the sysop (or steward) who administered the block"
        if self:
            return 'steward '*self.main['global'] + self.main['by']
        
    def done_string(self):
        "This function returns a string that indicates that the user was blocked"
        if self:
            return '{{done}} - %s is voor %s geblokkeerd door %s. Dank voor de melding. ~~~~'%(self.blocked(), self.duration(), self.get_name())
        
    def blocked(self):
        "Get which IP's are blocked."
        if self:
            return self.main['user'] #Kijk na welke gebruiker er is geblokkeerd
    
    def duration(self):
        "Get how long the IP has been blocked"
        if not self:
            return None #Make sure this special case cannot accidentally leak
        dur = self.main['expiry'] - self.main['timestamp']
        #Divide the duration into smaller intervals
        years, months, weeks = dur//dt.timedelta(days=365), dur//dt.timedelta(days=28), dur//dt.timedelta(days=7)
        if years > 1000:
            return 'onbepaalde tijd' #An IP was indeffed
        if years:
            return '%d jaar'%years
        if months:
            return '%d maand(en)'%months
        if weeks:
            return '%d we(e)k(en)'%weeks
        days, hours = dur//dt.timedelta(hours=24), dur//dt.timedelta(hours=1)
        if days:
            return '%d dag(en)'%days
        return '%d uur'%hours        
    
    def __call__(self, process=True):
        "This function is used by MultiRequest, and handles the entire request at once"
        if process is True:
            self.check_blocked()
        if self:
            return self.blocked(), self.get_name(), self.duration()
    
class MultiRequest(c.GenMulti):
    def check_done(self):
        "Checks whether all requests were already handled or not."
        self.done = all((bool(i) for i in self.targets))
        return self.done
    
    def done_string(self):
        "This will generate a string that indicates whether all listed IP's are blocked"
        if not self:
            return None #Just stop this shit
        data = [i(False) for i in self.targets]
        ips, admins, times = [i[0] for i in data], [i[1] for i in data], [i[2] for i in data]
        if len(set(times)) > 1:
            times = 'bepaalde tijd'
        elif len(set(times)) == 1:
            times = next(iter(times))
        
        #Prepare the different parts that should come with a request
        ipstring = ', '.join(ips[:-1]) + ' & '*(len(ips) > 1) + ips[-1]
        admins = ', '.join(admins[:-1]) + ' & '*(len(admins) > 1) + admins[-1]
        return '{{done}} - %s is/zijn voor %s geblokkeerd door %s. Dank voor de melding.'%(ipstring, times, admins)
        

class Test(IPBLOK):
    "The function that should be put to testwiki"
    def __init__(self):
        super().__init__()
        self.name = 'Verzoekpagina'
        self.bot = c.TestBot()
    
    def format_date(self, date):
        "Overrides this with the conventions for testwiki"
        assert isinstance(date, str), "Please pass a string as the argument of format_nldate!"
        for k, l in c.Page.testdate.items():
                date = date.replace(k, l)
        return dt.datetime.strptime(date, '%d %m %Y') #this is the object that can actually do the job for us
