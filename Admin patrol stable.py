# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 18:10:03 2021

@author: Daniuu

This script provides some handy administrative tools, that could be used at the Dutch Wikipedia.
This bot uses designated OAuth keys (which are for obvious reasons stored in another file).
This script is designed to run under the account 'DaniuuBot'.
Some functions were specifically modified for this little tool.
"""
from Core import NlBot
import re #Regex
import datetime as dt #Import support for dates and times

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
    
    donetemp = {'done', 'd', 'nd'}
    
    def __init__(self, name, url):
        self.name, self.url = name, url
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

    def check_request_on_line(self, line, pattern=r'((diff=\d{1,9}\&)?oldid=\d{1,9}|Permalink:\d{1,9}|\{\{diff\|\d{1,9})'):
        "Checks whether the line passed as an argument contains any kind of requests"
        raw = re.findall(pattern, line) #this will unleash the regex on the poor little line
        z = [] #create a list to store all separate matches (and where we can leave out the empty matches if any)
        for i in raw: #Go through all returned matches
            if isinstance(i, (tuple, list)):
                for j in i: #check all separate elements of the tuple or list that was found
                    if j.strip(): #Check that j is not empty
                        z.append(j.strip())
            else: #We found a string or so, can just be added if not empty
                if i:
                    z.append(j)
        return z #Returns the list with non-empty matches of the regex
    
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
    
    def filter_queue(self):
        "This function will convert the strings in the queue to a requests that can be handled"
        if not self._queue:
            #This means that the split was not yet done
            self.separate()
        #manually_flagged = False #this is a parameter that should check whether a given reqeust has been flagged manually
        try:
            for i, j in enumerate(self._queue[1:]):
                #Skip the first one, this only contains a header for this section
                z = self.check_request_on_line(j)
                if z:
                    if i >= 1:
                        if manually_flagged is True: #the request has been flagged in a manual manner
                            self.requests['flagged'] = self.requests.get('flagged', []) + [(start, i + 1)]
                        else:
                            self.requests.update({l:(start, i + 1)})
                    l = tuple((Request(i) for i in z)) #Generate a tuple with the requests
                    start = i + 1
                    manually_flagged = False
                elif any(((('{{' + k + '}}') in j) for k in Page.donetemp)):
                    manually_flagged = True #Indicate that this request has been flagged manually
            
            #Process the request at the end of the queue
            if manually_flagged is True:
                self.requests['flagged'] = self.requests.get('flagged', []) + [(start, i + 2)]
            else:
                self.requests.update({l:(start, i + 2)})
        except UnboundLocalError:
            return None #Do nothing (this is due to the fact that the )
        return self.requests
    
    def check_queue_done(self):
        "Check which requests in the queue are done (and flags them accordingly)"
        if not self.requests:
            self.filter_queue()
        for i in self.requests:
            if not isinstance(i, str): #Ignore strings, these are only added for administrative purposes
                for j in i:
                    j.check_done(self.bot)
    
    def check_requests(self):
        'This function will check whether all requests are done, and can move the request to the next part'
        self.check_queue_done()
        sto = []# A list to store the indices that can be processed
        #First, process the requests that were marked manually
        sto += [(i, j, None) for i, j in self.requests.get('flagged', ())] #Generate a list of tuples with 'None' as third element
        
        #Now, process the requestst that can be flagged automatically
        for i in self.requests:
            if not isinstance(i, str): #These ones should be ignored (we can do the deletion first)
                if all((bool(j) for j in i)): #checks whether all requests have been handled
                    sto.append(self.requests[i] + (i[0].check_person(self.bot),)) #Add the desired indices to the list that will be processed later
        
        #Begin processing the requests that are done or flagged
        sto.sort() #Do in place sorting to make things easier
        for i, j, u in sto: #Query the indices and add the request to the 'done' section
            self._done += self._queue[i:j]
            if u is not None: #u is None indicates that the request was manually flagged
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
        def process(indices, matches): #Use a closure
            #The date was found, now convert it to a format that Python acutally understands
            date = matches[0]
            for k in Page.nldate:
                date = date.replace(k, Page.nldate[k])
            d = dt.datetime.strptime(date, '%d %m %Y') #this is the object that can actually do the job for us
            
            #check whether we can get rid of this request
            deltime = d + dt.timedelta(days=drm, hours=6) #Only remove the requests from 6 am onwards
            if deltime < now:
                l.append(indices)
            
        if not self._done:
            self.separate()
        #Filter the requests (see also above)
        l, start, now, mark = [], 1, dt.datetime.now(), False  #Check what time it is (mark is used to verify that we found a nice match)
        pat = r'(\d{1,2} ' + f'({"|".join(Page.nldate.keys())}) ' + r'\d{4})'
        for i, j in enumerate(self._done):
            if i > 1: #Ignore the first line (and second line, to make things easier)
                if self.check_request_on_line(j):
                    #We ended searching our current request, add it to the list if it can be deleted
                    if mark is False:
                        temp = self.check_request_on_line(self._done[i - 1].lower(), pat)
                        if temp:
                            matches = temp
                        else:
                            temp = self.check_request_on_line(j.lower(), pat)
                            if temp:
                                matches = temp
                    process((start, i), matches) #rely on the closure to process the request
                    start = i #Set for the processing of the next request
                    mark = False #Reset this

                if any(('{{%s}}'%k in j for k in Page.donetemp)):
                    #Process the request
                    mark = True
                    matches = self.check_request_on_line(j.lower(), pat)
        
        #Process the final request
        process((start, i + 1), matches)
        for i, j in l[::-1]:
            del self._done[i:j]
        return len(l) #Return the amount of requests that were deleted
                
    def update(self, logonly=False):
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
                    'nocreate':True,
                    'basetimestamp':self._timestamp}
        if logonly is False:
            result = self.bot.post(edit_dic) #Make the post request and store the output to check for eventual edit conflicts
            if 'error' in result: #An error occured
                if result['error']['code'] == 'editconflict':
                    print('An edit conflict occured during the processing. I will wait for ten seconds')
                    time.sleep(10)
                    print('Redoing the things.')
                    return self() #Rerun the script, we found a nice little new request
        print(f'Removed {y}, processed {z}') #Just some code for maintenance purposes
                
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
        if 'diff=' in inp and 'diff=prev' not in inp: #Beware for a very special case
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
                    self._user = i['user']
                    return i['user']
    
    def done_string(self):
        "This function will generate a string that can be used to indicate that the request has been done"
        return f"De versie(s) is/zijn verborgen door {self._user if self._user is not None else 'een moderator'}"

t = Page("Wikipedia:Verzoekpagina voor moderatoren/Versies verbergen", "https://nl.wikipedia.org/wiki/Wikipedia:Verzoekpagina_voor_moderatoren/Versies_verbergen")
t(True) #Script in log-only 