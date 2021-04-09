# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 18:10:03 2021

@author: Daniuu

This script provides some handy administrative tools, that could be used at the Dutch Wikipedia.
This bot uses designated OAuth keys (which are for obvious reasons stored in another file).
This script is designed to run under the account 'DaniuuBot'.
Some functions were specifically modified for this little tool.
"""

import requests
import urllib
import time
import re #Regex
import datetime as dt #Import support for dates and times
from requests_oauthlib import OAuth1

class Page:
    "This is a class that allows the processing of a given request page"
    testdate = {'january':'01',
            'february':'02',
            'march':'03',
            'april':'04',
            'may':'05',
            'june':'06',
            'july':'07',
            'august':'08',
            'september':'09',
            'october':'10',
            'november':'11',
            "december":'12'}
    
    donetemp = {'done', 'd', 'nd'}
    
    def __init__(self, name, url):
        self.name, self.url = name, url
        self._content = []
        self._preamble, self._queue, self._done = [], [], [] #three lists for three parts of the request page
        self.requests = {} #This is a list of requests that are in the queue
        self.bot = TestBot() #Initialize a bot to do operations on Testwiki
        self.id = None
    
    def __str__(self):
        return self.name
    
    def get_page_content(self):
        "This function will get the last revision of the request page"
        d = {'action':'query',
             'prop':'revisions',
             'titles':self.name,
             'rvprop':'content|ids',
             'rvlimit':1,
             'rvdir':'older'}
        jos = self.bot.get(d)['query']['pages']
        self.id = int(next(iter(jos.keys())))
        temp = next(iter(jos.values()))['revisions'][0]['*'].split('\n')
        self._content = [i.strip() for i in temp if i.strip()]
        return self._content
    
    def separate(self, pend='Nieuwe verzoeken', hstart='Afgehandelde verzoeken'):
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
    
    def filter_queue(self, pattern=r'((diff=\d{1,7}\&)?oldid=\d{1,7}|Permalink:\d{1,7}|\{\{diff\|\d{1,7})'):
        "This function will convert the strings in the queue to a requests that can be handled"
        if not self._queue:
            #This means that the split was not yet done
            self.separate()
        #start = 1
        try:
            for i, j in enumerate(self._queue[1:]):
                #Skip the first one, this only contains a header for this section
                zraw = re.findall(pattern, j)
                z = []
                for k in zraw:
                    if isinstance(k, (tuple, list)):
                        z += list(k)
                    else:
                        z.append(k)
                z = [k for k in z if k]
                if z:
                    if i > 1:
                        self.requests.update({l:(start, i + 1)})
                    l = tuple((Request(i) for i in z)) #Generate a tuple with the requests
                    start = i + 1
            self.requests.update({l:(start, i + 2)})
        except UnboundLocalError:
            return None
        return self.requests
    
    def check_queue_done(self):
        if not self.requests:
            self.filter_queue()
        for i in self.requests:
            for j in i:
                j.check_done(self.bot)
    
    def check_requests(self):
        'This function will check whether all requests are done, and can move the request to the next part'
        self.check_queue_done()
        sto = []
        for i in self.requests:
            if all((bool(j) for j in i)):
                sto.append(self.requests[i] + (i[0].check_person(self.bot),)) #Add the desired indices to the list that will be processed later
        sto.sort() #Do in place sorting to make things easier
        for i, j, u in sto: #Query the indices and add the request to the 'done' section
            self._done += self._queue[i:j]
            pre = self._queue[j - 1].split()[0]
            if "*" in pre:
                prefix = '*'*(pre.count('*') + 1)
            else:
                prefix = ':'
            self._done.append(prefix + '{{done}} - ' + f'Gevraagde versie(s) zijn verborgen door {u}. Dank voor de melding. ~~~~')
        for i, j, _ in sto[::-1]: #Scan in reverse order - this will make the deletion sequence more logical
            del self._queue[i:j]
        return len(sto) #Return the number of processed requests
    
    def check_removal(self, tz=('utc', 'cet', 'cest'), drm=1):
        'This function will check which lines could be removed (after drm days).'
        if not self._done:
            self.separate()
        #Filter the requests (see also above)
        l, start, now = [], 1, dt.datetime.now()  #Check what time it is
        pat = r'(\d{1,2} ' + f'({"|".join(Page.testdate.keys())}) ' + r'\d{4})'
        for i, j in enumerate(self._done):
            if i > 0:
                if any(('{{%s}}'%k in j for k in Page.donetemp)):
                    #Process the request
                    matches = re.findall(pat, j.lower())
                    #The date was found, now convert it to a format that Python acutally understands
                    date = matches[0][0]
                    for k in Page.testdate:
                        date = date.replace(k, Page.testdate[k])
                    d = dt.datetime.strptime(date, '%d %m %Y') #this is the object that can actually do the job for us
                    
                    #check whether we can get rid of this request
                    deltime = d + dt.timedelta(days=drm, hours=6) #Only remove the requests from 6 am onwards
                    if deltime < now:
                        l.append((start, i + 1))
                    start = i + 1 #Set for the processing of the next request
        for i, j in l[::-1]:
            del self._done[i:j]
        return len(l) #Return the amount of requests that were deleted
                
    def update(self):
        "This function will update the content of the page"
        y = self.check_removal() #How many requests are deleted
        z = self.check_requests()
        t = ('\n'.join(self._preamble),
             '\n'.join(self._queue),
             '\n'.join(self._done))
        new = '\n'.join(t)
        
        #Prepare the edit summary
        summary = (f'{z} gemarkeerd als afgehandeld' if z else '') + (' & '*(bool(y*z))) + (f'{y} weggebezemd' if y else '')
        edit_dic = {'action':'edit',
                    'pageid':self.id,
                    'text':new,
                    'summary':summary,
                    'bot':True,
                    'minor':True,
                    'nocreate':True}
        self.bot.post(edit_dic) #Make the post request
                
class Request:
    "This object class will implement the main functionalities for a certain request"
    def __init__(self, target):
        self.target = self.process(target) #This object stores the main target (this could be an oldid)
        self.done, self.trash = False, False #this indicates whether 
        self._user = None #Fill in the user who processed the request
        self._page = None #Store the name of the page
        
    def __bool__(self):
        return self.done #This function will return whether the request was done or not
    
    def clean(self):
        "This function checks whether the reequest can be deleted"
        return self.trash
    
    def __str__(self):
        return str(self.target)
    
    def __repr__(self): #Not really what it should be
        return str(self.target)
    
    def process(self, inp):
        "This function will process the input fed to the constructor"
        if 'diff=' in inp: #Beware for a very special case
            return int(inp.split('&')[0].lower().replace('diff=', '').strip())
        return int(inp.lower().replace('oldid=', '').replace('permalink:', '').replace('diff', ''))
    
    def check_done(self, bot):
        if self.done is False:
            "This function will check whether the request has been processed"
            dic = {'action':'query',
                   'prop':'revisions',
                   'revids':self.target,
                   'rvprop':'content|timestamp|ids'}
            out = bot.get(dic)
            t = next(iter(next(iter(out.get('query').values())).values()))
            self._page = t['title']
            p = t['revisions'][0]
            if 'texthidden' in p:
                self.done = True
           
    def check_person(self, bot):
        'This function will check who did the request'
        dic = {'action':'query',
               'list':'logevents',
               'leprop':'user|details',
               'letype':'delete',
               'leaction':'delete/revision',
               'letitle':self._page}
        out = bot.get(dic)['query']['logevents']
        for i in out:
            k = i['params']
            if self.target in k['ids']: #the revision involved was queried here
                if 'content' in k['new']: #Will check whether the content of the revision was removed
                    return i['user']
