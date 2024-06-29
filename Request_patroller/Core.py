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
from toolforge import set_user_agent  # To set our user agent to something nicer
import datetime as dt  # Import support for dates and times
import re
import Bot_settings as bs

# Before taking any actions, change the UA to something nicer
set_user_agent('Daniuu-Bot')


# Functionality to allow logging
def clear_log_file(file):
    with open(file, 'w', encoding='utf8') as blankfile:
        blankfile.write('%s\n' % (dt.datetime.utcnow()))


def log(file, text):
    with open(file, 'a') as logfile:
        logfile.write(text.rstrip() + '\n')


class Bot:
    'This class is designed to facilitate all interactions with Wikipedia (and to get the processing functions out of other calsses)'
    max_edit = 1  # The maximum number of edits that a single bot can do per minute

    def __init__(self, api, m=None):
        'Constructs a bot, designed to interact with one Wikipedia'
        self.api = api
        self.ti = []  # A list to store the time stamps of the edits in
        self._token = None  # This is a token that is handy
        self._auth = None  # The OAuth ID (this is the token that will allow the auth - store this for every bot)
        self._max = Bot.max_edit if m is None else m  # this value is set, and can be changed if a bot bit would be granted
        self._tt = None

    def __str__(self):
        return self.api.copy()

    def verify_OAuth(self, file="Operational.txt"):
        'This function will verify whether the OAuth-auth has been configured. If not, it will do the configuration.'
        if self._auth is None:
            try:
                with open(file, 'r') as secret:
                    self._auth = OAuth1(*[i.strip() for i in secret][
                                         1::2])  # This is the reason why those keys should never be published
            except FileNotFoundError:  # A workaround for the shell file @toolforge
                from os import getcwd
                file = getcwd() + '/DaniuuBot/' + file  # An attempt to fix a particular bug
                with open(file, 'r') as secret:
                    self._auth = OAuth1(*[i.strip() for i in secret][1::2])

    def verify_token(self):
        if self._token is None:
            self.get_token()
        elif float(time.time()) - self._token[1] > 8:
            self.get_token()  # Tokens expire after approximately 8 seconds, so generate a new one
        return self._token[0]

    def get(self, payload):
        "This function will provide functionality that does all the get requests"
        self.verify_OAuth()
        payload['format'] = 'json'  # Set the output format to json
        return requests.get(self.api, params=payload, auth=self._auth, timeout=31).json()

    def get_token(self, t='csrf', n=0, store=True):
        'This function will get a token'
        assert isinstance(t, str), 'Please provide a string as a token!'
        pay = {'action': 'query',
               'meta': 'tokens',
               'type': t}
        z = self.get(pay), float(time.time())
        try:
            if store is True:
                self._token = z[0]['query']['tokens']['%stoken' % t], z[1]
                return self._token[0]
            else:
                return self._token[0]  # Just return the token
        except KeyError:
            assert n <= 1, 'Cannot generate the requested token'
            return self.get_token(t, n + 1)

    def post(self, params):
        assert 'action' in params, 'Please provide an action'
        t = float(time.time())
        self.ti = [i for i in self.ti if i >= t - 60]  # Clean this mess
        if len(self.ti) >= Bot.max_edit:  # Check this again, after doing the cleaning
            print('Going to sleep for a while')
            time.sleep(20)  # Fuck, we need to stop
            return self.post(params)  # run the function again - but: with a delay of some 60 seconds
        if 'token' not in params:  # Place this generation of the key here, to avoid having to request too many tokens
            params['token'] = self.verify_token()  # Generate a new token
        params['format'] = 'json'
        params['maxlag'] = 5  # Using the standard that's implemented in PyWikiBot
        self.ti.append(float(time.time()))
        k = requests.post(self.api, data=params, auth=self._auth, timeout=31).json()
        if 'error' in k:
            print('An error occured somewhere')  # We found an error
            print(k)
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


class VlsBot(Bot):
    def __init__(self):
        super().__init__('https://vls.wikipedia.org/w/api.php')


# Below: classes that implement general page patrollers and requests
class Page:
    "This is a class that allows the processing of a given request page"
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

    testdate = {'January': '01',
                'February': '02',
                'March': '03',
                'April': '04',
                'May': '05',
                'June': '06',
                'July': '07',
                'August': '08',
                'September': '09',
                'October': '10',
                'November': '11',
                'December': '12'}

    donetemp = ('done', 'd', 'nd', 'Not done')  # Last ones are typical for nlwiki

    def __init__(self,
                 name,
                 testing=False):
        self.name = name
        self._content = []
        self._preamble, self._queue, self._done = [], [], []  # three lists for three parts of the request page
        self.requests = {}  # This is a list of requests that are in the queue
        self.bot = NlBot()  # Initialize a bot to do operations on Testwiki
        self.id = None
        self._logfile = 'Log.txt'

        # Code implemented solely for testing purposes
        # A boolean value will be used to check whether we are testing the bot or fully operational
        # The boolean is called by the functions updating the final page
        # Furthermore, the boolean is checked by the function that gets the page content
        # If set to True, the Bot will operate in its testing mode!
        self._testing = testing
        # If the bot is called in its testing mode, write this to the terminal
        if self._testing is True:
            print('CAUTION: BOT CALLED IN TESTING MODE')

        # Extension 20240626 - to process requests with a header
        self._headerpattern = r'={3,}\s*[^=]+\s*={3,}'

    def __str__(self):
        return self.name

    def __call__(self, logonly=False, force_removal=False):
        return self.update(logonly, force_removal=force_removal)

    def get_page_content(self):
        """This function will get the last revision of the request page"""
        log(self._logfile, 'Starting to parse the request page')
        if self._testing is False:
            # Bot is called in operational mode
            d = {'action': 'query',
                 'prop': 'revisions',
                 'titles': self.name,
                 'rvprop': 'content|ids|timestamp',
                 'rvlimit': 1,
                 'rvdir': 'older'}
            jos = self.bot.get(d)['query']['pages']
            self.id = int(next(iter(jos.keys())))
            self._timestamp = jos[str(self.id)]['revisions'][0]['timestamp']  # To check for an eventual edit conflict
            temp = next(iter(jos.values()))['revisions'][0]['*'].split('\n')
        elif self._testing is True:
            # This code is solely executed if the bot is called in its Test mode
            with open(bs.test_input, 'r', encoding='utf8') as inputfile:
                temp = inputfile.readlines()  # We don't need to query the database, just some text
        # Final code (always executed)
        self._content = [i.strip() for i in temp if i.strip()]
        log(self._logfile, 'Done getting the contents from the request page')
        return self._content

    def separate(self, pend, hstart):
        """This function will separate the contents of the page into preamble, actual requests and handled ones"""
        log(self._logfile, 'Starting separating page into its composing sections')
        if not self._content:  # The list is still empty
            self.get_page_content()
        t = [i.replace('=', '').strip() for i in self._content]  # Generate a list with all the levels neutralized
        try:
            pe, hs = t.index(pend), t.index(hstart)
        except ValueError:
            # This indicates that something wrong was added
            print('Watch out! The required headers were not found in the list')
            return None
        self._preamble = self._content[:pe]
        self._queue = self._content[pe:hs]
        self._done = self._content[hs:]
        log(self._logfile, 'Done separating!')
        return self._queue

    def check_queue_done(self):
        """Check which requests in the queue are done (and flags them accordingly)"""
        if not self.requests:
            self.filter_queue()
        log(self._logfile, 'Now going through the requests and checking whether they are done')
        for i in self.requests:
            if not isinstance(i, str):  # Ignore strings, these are only added for administrative purposes
                log(self._logfile, 'Checking request %s' % i)
                i.check_done()
        log(self._logfile, 'DONE checking requests')

    def update(self, logonly=False, force_removal=False):
        "This function will update the content of the page"
        print('Bot was called at ' + str(dt.datetime.now()))
        # Following issue of 2 February 2024 (IPBLOK - https://w.wiki/93qd)
        # We will only clear the page between 4:00 and 4:18 UTC
        log(self._logfile, 'Starting update process')
        current_time = dt.datetime.utcnow()
        if (current_time.hour == 4 and 0 <= current_time.minute <= 17) or (force_removal is True):
            log(self._logfile, 'Starting checking what needs to be removed')
            y = self.check_removal()  # How many requests are deleted
            log(self._logfile, 'Removal fully processed')
        else:
            y = 0  # Automatic way to bypass clearing requests & repeated instances
        log(self._logfile, 'Patrolling new requests')
        z = self.check_requests()
        log(self._logfile, 'Done checking new requests')
        t = ('\n'.join(self._preamble),
             '\n'.join(self._queue),
             '\n'.join(self._done))
        new = '\n'.join(t)
        log(self._logfile, 'New page text has been prepared')

        # Following request made at https://w.wiki/7M8A
        # Bot will automatically stop if {{nobots}} is added to the page
        temp_concent = [i.lower() for i in self._content]
        for line in temp_concent:
            if any((i.lower() in line for i in bs.abort_strings)):
                # If this code is called, abort all running and don't make any further requests
                print('\nBOT FORCIBLY TERMINATED DUE TO STOP STRINGS\n')
                return None  # Make sure the program stops here
        del temp_concent  # Checks are done, we don't need to store the content in lowercase anymore

        if y == 0 and z == 0 and self._testing is False:
            # Main function of the code: avoid making useless requests to the API
            # Requests are considered useless if no changes will be made
            # This code is only executed in operational mode
            # In testing mode, the edit API is not called
            # In testing mode, we want the output to be updated in every iteration
            # Hence, check bypassed in testing mode
            print('Nothing to be done!')
            log(self._logfile, 'Stopping, no need to do anything')
            print(self.requests)
            return self.print_termination()  # No need to go through the remainder of the function

        # Determine whether there are still requests open.
        remain = len(self.requests) - z
        remain *= remain >= 0

        # Prepare the edit summary
        # summary = ('%d verzoek(en) gemarkeerd als afgehandeld'%z if z else '') + (' & '*(bool(y*z))) + ('%d verzoek(en) weggebezemd'%y if y else '')
        tup = (('%d verzoek(en) gemarkeerd als afgehandeld' % z) if z else '',
               ('%d verzoek(en) weggebezemd' % y) if y else '',
               ('%d verzoek(en) nog af te handelen' % remain))
        summary = ' & '.join((i for i in tup if i))
        # This code will update the page on the wiki
        # The code can only be executed if the bot is called in "operational" mode
        # The bot is operational if self._testing is set to False
        if self._testing is False:
            log(self._logfile, 'Preparing to post the new content')
            edit_dic = {'action': 'edit',
                        'pageid': self.id,
                        'text': new,
                        'summary': summary,
                        'bot': True,
                        # 'minor':True,  # Not needed if all edits are marked as "small" - set on the wiki
                        'nocreate': True,
                        'basetimestamp': self._timestamp}
            # This code is only executed when the bot is ran in operational mode
            # If the bot is set to log-only, no changes will be pushed to the wiki
            if logonly is False:
                result = self.bot.post(
                    edit_dic)  # Make the post request and store the output to check for eventual edit conflicts
                log(self._logfile, 'Posted!')
                if 'error' in result:  # An error occured
                    if result['error']['code'] == 'editconflict':
                        print('An edit conflict occured during the processing. I will wait for ten seconds')
                        print('Redoing the things.')
                        log(self._logfile, 'Recursion starting')
                        return self()  # Rerun the script, we found a nice little new request
            else:
                print('Script is called in log-only, no changes will be made.')
            print('Removed %d, processed %d, %d remaining' % (y, z, remain))  # Just some code for maintenance purposes
            log(self._logfile, 'DONE!')
        # The bot can also be called in its test mode
        # In test mode, no edits to the wiki should be made
        # All changes are pushed to a dedicated output file, defined in the Bot's settings
        elif self._testing is True:
            with open(bs.test_output, 'w', encoding='utf8') as outputfile:
                outputfile.write(new)
            # Inform the operator that the bot wrote its output to a test location
            print('Bot update function was called in test mode!')
            # Inform user about the location of their output
            # This function requires Python 3.6+
            print('Bot output was written to %s.' % bs.test_output)
            # Print the edit summary as a service to the tester
            print(summary)
        # End of the testing section
        # The bot will now write a message to the terminal
        # The message indicates that the update run was performed without errors
        self.print_termination()
        log(self._logfile, 'DONE')

    def print_termination(self):
        print('Bot terminated successfully at ' + str(dt.datetime.now()) + '\n')

    def filter_date(self, line):
        log(self._logfile, 'Filtering data for %s' % line)
        pattern = r'(\d{1,2} (%s) \d{4})' % ('|'.join(Page.nldate))
        return re.findall(pattern, line)

    def format_date(self, date):
        """This function formats a date in the nlwiki format. The returned date only contains information on the day,
        month, and year the request was passed """
        assert isinstance(date, str), "Please pass a string as the argument of format_date!"
        return dt.datetime.strptime(self.replace_months(date),
                                    '%d %m %Y')  # this is the object that can actually do the job for us

    def replace_months(self, date):
        "This function replaces the names of months in the strings"
        log(self._logfile, 'Replacing months')
        for i, j in Page.nldate.items():
            date = date.replace(i, j)
        log(self._logfile, 'Don replacing months')
        return date

    def clear_lines(self, parent, lines):
        "This function deletes the given lines from the parent list"
        log(self._logfile, 'Starting deletion of lines %s' % lines)
        for i, j in sorted(lines, reverse=True):
            del parent[i:j]
        log(self._logfile, 'DONE deleting lines')
        return len(lines)

    def get_date_for_lines(self, lines):
        "This function will return the most recent contribution date that corresponds with a given request."
        for k in lines[::-1]:  # Run the inverse
            try:
                date_temp = self.filter_date(k)[0][0]  # Get the date on that line (using Regex)
                return self.format_date(date_temp)  # Convert the found date into an actual DateTime
            except IndexError:  # It's easier to ask for forgiveness, as this sin can be forgiven easily.
                date_temp = None
        # No date was found, use an emergency procedure
        now = dt.datetime.utcnow()  # Get current UTC time
        if 4 <= now.hour <= 6:
            return dt.datetime.today() - dt.timedelta(days=1)
        return dt.datetime.today()

    # Adjustment 20240626 - handy function for spotting headers on a line
    def header_on_line(self, line):
        if not isinstance(line, str):
            raise TypeError('Only pass strings to the header_on_line method!')
        return re.match(self._headerpattern, line.strip()) is not None


class GenReq:
    def __init__(self, target, types=(int,)):
        self.target = self.process(target)  # This object stores the main target (this could be an oldid)
        self.done = False  # this indicates whether the request was already handled or not
        self._user = None  # Fill in the user who processed the request
        self._page = None  # Store the name of the page
        self.deleted = False
        if not isinstance(self.target, types):
            raise TypeError('The target should be of the specified type!')

    def __bool__(self):
        return self.done or self.deleted  # This function will return whether the request was done or not

    def __str__(self):
        return str(self.target)

    def __repr__(self):  # Not really what it should be
        return str(self.target)

    def __eq__(self, other):
        return self.target == other.target

    def __hash__(self):
        return self.target.__hash__()

    def done_string(self):
        "This function will generate a string that can be used to indicate that the request has been done"
        martin = self._user if self._user is not None else 'een moderator'
        return "De versie(s) is/zijn verborgen door %s." % martin

    def convert_api_date(self, stamp):
        "Function converts a date that is sent through the API"
        try:
            return dt.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return dt.datetime(9999, 12, 31)

    def is_deleted(self):
        "Checks whether the target got deleted before"
        return self.deleted is True


class GenMulti:
    def __init__(self, req):
        assert all((isinstance(i, GenReq) for i in req)), 'Please only provide requests!'
        self.targets = list(set(req))  # Use a tuple here
        self.done = False  # This indicates whether the request was done
        self._user = None
        self.deleted = False  # A parameter tracking whether the target page got deleted

    def __str__(self):
        return str(self.targets + self.users)

    def __repr__(self):
        return str(self)

    def __bool__(self):
        return self.done or self.deleted

    def __hash__(self):
        "This function will provide a nice hash"
        return tuple(self.targets).__hash__()

    def done_string(self):
        "This function will generate a string that can be used to indicate that the request has been done"
        martin = self._user if self._user is not None else 'een moderator'
        return "De versie(s) is/zijn verborgen door %s." % martin

    def is_deleted(self):
        "Checks whether the target got deleted before"
        return self.deleted is True
