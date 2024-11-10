"""
File that governs all common files for the request patrollers

Functions are mainly related to patrolling request pages
"""

import re
import Bot_settings as bs
from Core import log, NlBot
import datetime as dt
import nldate_utils as nld


# Below: classes that implement general page patrollers and requests
class Page:
    "This is a class that allows the processing of a given request page"
    nldate = nld.nldate

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
        self._inter = []  # Addition 20241102 - to get backwards compatibility with WP:REGBLOK handler
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

        # Extension 20241109 - to force a bot to renew the content of the page
        # Application: flagging locked accounts on REGBLOK
        self._force_processing = False

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
        # Method just makes sure that all requests check whether they're acutally done
        # Methods that check whether a request is done ==> implemented in the Request class
        if not self.requests:
            self.filter_queue()
        log(self._logfile, 'Now going through the requests and checking whether they are done')
        for i in self.requests:
            if not isinstance(i, str):  # Ignore strings, these are only added for administrative purposes
                log(self._logfile, 'Checking request %s' % i)
                i.check_done()
        log(self._logfile, 'DONE checking requests')

    def process_intermediate(self):
        return None  # Just a dummy function

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

        # 20241102 - REGBLOK has an intermediate section - also handle that one as well
        self.process_intermediate()

        t = ('\n'.join(self._preamble),
             '\n'.join(self._queue),
             '\n'.join(self._inter),
             '\n'.join(self._done))
        new = '\n'.join(t)
        log(self._logfile, 'New page text has been prepared')

        # Following request made at https://w.wiki/7M8A
        # Bot will automatically stop if {{nobots}} is added to the page
        temp_content = [i.lower() for i in self._content]
        for line in temp_content:
            if any((i.lower() in line for i in bs.abort_strings)):
                # If this code is called, abort all running and don't make any further requests
                print('\nBOT FORCIBLY TERMINATED DUE TO STOP STRINGS\n')
                return None  # Make sure the program stops here
        del temp_content  # Checks are done, we don't need to store the content in lowercase anymore

        if y == 0 and z == 0 and self._testing is False and self._force_processing is False:
            # Main function of the code: avoid making useless requests to the API
            # Requests are considered useless if no changes will be made
            # This code is only executed in operational mode
            # In testing mode, the edit API is not called
            # In testing mode, we want the output to be updated in every iteration
            # Hence, check bypassed in testing mode
            print('Nothing to be done!')
            log(self._logfile, 'Stopping, no need to do anything')
            print(self.requests)  # For logging on Toolforge
            return self.print_termination()  # No need to go through the remainder of the function

        # Determine whether there are still requests open.
        remain = len(self.requests) - z
        remain *= remain >= 0

        # Prepare the edit summary
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

        # Addition 20241109 - we processed the page, so we can do some resetting
        self._force_processing = False  # Reset variable

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
