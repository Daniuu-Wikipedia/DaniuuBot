# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 21:22:05 2021

@author: Daniuu

This is the general code that the all applications will use when being deployed for testing purposes.
It just contains a general instance of a Bot, and some handy subclasses that are preset for the main wikis where the bot will be deployed
"""
import requests
from requests_oauthlib import OAuth1
import time
import datetime as dt #Import support for dates and times
import re

class Bot:
    'This class is designed to facilitate all interactions with Wikipedia (and to get the processing functions out of other calsses)'
    max_edit = 1 #The maximum number of edits that a single bot can do per minute
    
    def __init__(self, api, m=None):
        'Constructs a bot, designed to interact with one Wikipedia'
        self.api = api
        self.ti = [] #A list to store the time stamps of the edits in
        self._token = None #This is a token that is handy
        self._auth = None #The OAuth ID (this is the token that will allow the auth - store this for every bot)
        self._max = Bot.max_edit if m is None else m #this value is set, and can be changed if a bot bit would be granted
        self._tt = None
    
    def __str__(self):
        return self.api.copy()
    
    def verify_OAuth(self, file="Operational.txt"):
        'This function will verify whether the OAuth-auth has been configured. If not, it will do the configuration.'
        if self._auth is None:
            with open(file, 'r') as secret:
                self._auth = OAuth1(*[i.strip() for i in secret][1::2]) #This is the reason why those keys should never be published
    
    def verify_token(self):
        if self._token is None:
            self.get_token()
        elif float(time.time()) - self._token[1] > 8:
            self.get_token() #Tokens expire after approximately 8 seconds, so generate a new one
        return self._token[0]
    
    def get(self, payload):
        "This function will provide functionality that does all the get requests"
        self.verify_OAuth()
        payload['format'] = 'json' #Set the output format to json
        return requests.get(self.api, params=payload, auth=self._auth).json()
    
    def get_token(self, t='csrf', n=0, store=True):
        'This function will get a token'
        assert isinstance(t, str), 'Please provide a string as a token!'
        pay = {'action':'query',
               'meta':'tokens',
               'type':t}
        z = self.get(pay), float(time.time())
        try:
            if store is True:
                self._token = z[0]['query']['tokens']['%stoken'%t], z[1]
                return self._token[0]
            else:
                return self._token[0] #Just return the token
        except KeyError:
            assert n <= 1, 'Cannot generate the requested token'
            return self.get_token(t, n + 1)
    
    def post(self, params):
        assert 'action' in params, 'Please provide an action'
        t = float(time.time())
        self.ti = [i for i in self.ti if i >= t - 60] #Clean this mess
        if len(self.ti) >= Bot.max_edit: #Check this again, after doing the cleaning
            print('Going to sleep for a while')
            time.sleep(20) #Fuck, we need to stop
            return self.post(params) #run the function again - but: with a delay of some 60 seconds
        if 'token' not in params: #Place this generation of the key here, to avoid having to request too many tokens
            params['token'] = self.verify_token() #Generate a new token
        params['format'] = 'json'
        params['maxlag'] = 5 #Using the standard that's implemented in PyWikiBot
        self.ti.append(float(time.time()))
        k = requests.post(self.api, data=params, auth=self._auth).json()
        if 'error' in k:
            print('An error occured somewhere') #We found an error
            if 'code' in k['error'] and 'maxlag' in k['error']['code']:
                print('Maxlag occured, please try to file the request at a later point in space and time.')
        return k
        
class WikidataBot(Bot):
    def __init__(self):
        super().__init__('https://www.wikidata.org/w/api.php')

class CommonsBot(Bot):
    def __init__(self):
        super().__init__('https://commons.wikimedia.org/w/api.php')

class MetaBot(Bot):
    def __init__(self):
        super().__init__('https://meta.wikimedia.org/w/api.php')

class NlBot(Bot):
    def __init__(self):
        super().__init__('https://nl.wikipedia.org/w/api.php')
        
class BetaBot(Bot):
    'This is a bot that will allow for editing from the BetaWiki of the Dutch Wikipedia'
    def __init__(self):
        super().__init__("https://nl.wikipedia.beta.wmflabs.org/api.php")
        
    def verify_OAuth(self):
        super().verify_OAuth('Beta.txt')
        
class TestBot(Bot):
    def __init__(self):
        super().__init__('https://test.wikipedia.org/w/api.php')
        
#Below: classes that implement general page patrollers and requests
class Page:
    "This is a class that allows the processing of a given request page"
    nldate = {'jan':'01',
            'feb':'02',
            'mrt':'03',
            'apr':'04',
            'mei':'05',
            'jun':'06',
            'jul':'07',
            'aug':'08',
            'sep':'09',
            'okt':'10',
            'nov':'11',
            "dec":'12'}
    
    testdate = {'January':'01',
                'February':'02',
                'March':'03',
                'April':'04',
                'May':'05',
                'June':'06',
                'July':'07',
                'August':'08',
                'September':'09',
                'October':'10',
                'November':'11',
                'December':'12'}
    
    donetemp = ('done', 'd', 'nd', 'Not done') #Last ones are typical for nlwiki
    
    def __init__(self, name):
        self.name = name
        self._content = []
        self._preamble, self._queue, self._done = [], [], [] #three lists for three parts of the request page
        self.requests = {} #This is a list of requests that are in the queue
        self.bot = NlBot() #Initialize a bot to do operations on Testwiki
        self.id = None
    
    def __str__(self):
        return self.name
    
    def __call__(self, logonly=False):
        return self.update(logonly)
    
    def get_page_content(self):
        "This function will get the last revision of the request page"
        d = {'action':'query',
             'prop':'revisions',
             'titles':self.name,
             'rvprop':'content|ids|timestamp',
             'rvlimit':1,
             'rvdir':'older'}
        jos = self.bot.get(d)['query']['pages']
        self.id = int(next(iter(jos.keys())))
        self._timestamp = jos[str(self.id)]['revisions'][0]['timestamp'] #To check for an eventual edit conflict
        temp = next(iter(jos.values()))['revisions'][0]['*'].split('\n')
        self._content = [i.strip() for i in temp if i.strip()]
        return self._content
    
    def separate(self, pend, hstart):
        "This function will separate the contents of the page into preamble, actual requests and handled ones"
        if not self._content: #The list is still empty
            self.get_page_content()
        t = [i.replace('=', '').strip() for i in self._content] #Generate a list with all the levels neutralized
        try:
            pe, hs = t.index(pend), t.index(hstart)
        except ValueError:
            #This indicates that something wrong was added
            print('Watch out! The required headers were not found in the list')
            return None
        self._preamble = self._content[:pe]
        self._queue = self._content[pe:hs]
        self._done = self._content[hs:]
        return self._queue

    def check_queue_done(self):
        "Check which requests in the queue are done (and flags them accordingly)"
        if not self.requests:
            self.filter_queue()
        for i in self.requests:
            if not isinstance(i, str): #Ignore strings, these are only added for administrative purposes
                i.check_done()
    

    def update(self, logonly=False):
        "This function will update the content of the page"
        print('Bot was called at ' + str(dt.datetime.now()))
        y = self.check_removal() #How many requests are deleted
        z = self.check_requests()
        t = ('\n'.join(self._preamble),
             '\n'.join(self._queue),
             '\n'.join(self._done))
        new = '\n'.join(t)
        
        if y == 0 and z == 0:
            print('Nothing to be done!')
            print(self.requests)
            return self.print_termination() #No need to go through the remainder of the function
        
        #Prepare the edit summary
        summary = ('%d verzoeken gemarkeerd als afgehandeld'%z if z else '') + (' & '*(bool(y*z))) + ('%d verzoeken weggebezemd'%y if y else '')
        edit_dic = {'action':'edit',
                    'pageid':self.id,
                    'text':new,
                    'summary':summary,
                    'bot':True,
                    'minor':True,
                    'nocreate':True,
                    'basetimestamp':self._timestamp}
        if logonly is False:
            result = self.bot.post(edit_dic) #Make the post request and store the output to check for eventual edit conflicts
            if 'error' in result: #An error occured
                if result['error']['code'] == 'editconflict':
                    print('An edit conflict occured during the processing. I will wait for ten seconds')
                    print('Redoing the things.')
                    return self() #Rerun the script, we found a nice little new request
        else:
            print('Script is called in log-only, no changes will be made.')
        print('Removed %d, processed %d'%(y, z)) #Just some code for maintenance purposes
        self.print_termination()
        
    def print_termination(self):
        print('Bot terminated successfully at ' + str(dt.datetime.now()) + '\n')
    
    def filter_date(self, line):
        pattern = r'(\d{1,2} (%s) \d{4})'%('|'.join(Page.nldate))
        return re.findall(pattern, line)
        
    def format_date(self, date):
        "This function formats a date in the nlwiki format"
        assert isinstance(date, str), "Please pass a string as the argument of format_nldate!"
        return dt.datetime.strptime(date, '%d %m %Y') #this is the object that can actually do the job for us

class GenReq:
    def __init__(self, target, types=(int,)):
        self.target = self.process(target) #This object stores the main target (this could be an oldid)
        self.done = False #this indicates whether the request was already handled or not
        self._user = None #Fill in the user who processed the request
        self._page = None #Store the name of the page
        if not isinstance(self.target, types):
            raise TypeError('The target should be of the specified type!')

    def __bool__(self):
        return self.done #This function will return whether the request was done or not
        
    def __str__(self):
        return str(self.target)
    
    def __repr__(self): #Not really what it should be
        return str(self.target)
    
    def __eq__(self, other):
        return self.target == other.target
    
    def __hash__(self):
        return self.target.__hash__()

    def done_string(self):
        "This function will generate a string that can be used to indicate that the request has been done"
        martin = self._user if self._user is not None else 'een moderator'
        return "De versie(s) is/zijn verborgen door %s."%martin
    
    def convert_api_date(self, stamp):
        "Function converts a date that is sent through the API"
        try:
            return dt.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return dt.datetime(9999, 12, 31)

class GenMulti:
    def __init__(self, req):
        assert all((isinstance(i, GenReq) for i in req)), 'Please only provide requests!'
        self.targets = list(req) #Use a tuple here
        self.done = False #This indicates whether the request was done
        self._user = None
    
    def __str__(self):
        return str(self.targets + self.users)
    
    def __repr__(self):
        return str(self)
    
    def __bool__(self):
        return self.done

    def __hash__(self):
        "This function will provide a nice hash"
        return tuple(self.targets).__hash__()

    def done_string(self):
        "This function will generate a string that can be used to indicate that the request has been done"
        martin = self._user if self._user is not None else 'een moderator'
        return "De versie(s) is/zijn verborgen door %s."%martin

