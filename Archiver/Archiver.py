"""
Archive bot

This bot was developed following a request by Akoopal (for an archive bot that could deal with headers & subheaders)
@author: Daniuu

"""

# Main imports
import Core as c

# For each page, input: name of section to be archived, target directory

import requests
from requests_oauthlib import OAuth1
import time
from toolforge import set_user_agent  # To set our user agent to something nicer
import datetime as dt  # Import support for dates and times
import re
import pytz  # Timezone management
import General_settings as gs

# Before taking any actions, change the UA to something nicer
set_user_agent('Daniuu-Bot')


# Functionality to allow logging
def clear_log_file(file):
    with open(file, 'w', encoding='utf8') as blankfile:
        blankfile.write('%s\n' % (dt.datetime.utcnow()))


def log(file, text):
    with open(file, 'a') as logfile:
        logfile.write(text.rstrip() + '\n')


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

    timezone = pytz.timezone('Europe/Amsterdam')  # nlwiki uses Amsterdam time

    def __init__(self,
                 name,
                 archive_target,
                 testing=True):
        # Names of relevant pages
        self.archive_target = archive_target
        self.name = name

        # Store page content
        self._content = []
        # Different parts of the page...
        self._hot = []
        self.requests = {}  # This is a list of requests that are in the queue

        # The Bot that will perform the actions
        self.bot = c.NlBot()  # Initialize a bot to do operations on Testwiki
        self.id = None

        # File for logging
        self._logfile = 'Log.txt'
        # Code implemented solely for testing purposes
        # A boolean value will be used to check whether we are testing the bot or fully operational
        # The boolean is called by the functions updating the final page
        # Furthermore, the boolean is checked by the function that gets the page content
        # If set to True, the Bot will operate in its testing mode!
        self._testing = testing

        # Timestamp to check for edit conflicts
        self._timestamp = None

        # Properties to be read from the bot's settings
        # These include the level of headers to be archived & sections that need archiving
        # AT PRESENT: test values have been hardcoded!
        self._startsection = 'Afgehandelde verzoeken'
        self._endsection = '$END'
        self._level = 3
        self._passed_dates = 7

        # Store handy indices (improve memory-efficiency)
        self._startrule, self._endrule = None, None

        # Store indices that can be deleted
        self._delete = []

        # If the bot is called in its testing mode, write this to the terminal
        if self._testing is True:
            print('CAUTION: BOT CALLED IN TESTING MODE')

    # Property controlling testing
    @property
    def testing(self):
        return self._testing

    @testing.setter
    def testing(self, testing):
        if not isinstance(testing, bool):
            raise TypeError('testing must be a boolean')
        self._testing = testing

    # Utility to get the content of the page
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
            with open(gs.test_input, 'r', encoding='utf8') as inputfile:
                temp = inputfile.readlines()  # We don't need to query the database, just some text
        # Final code (always executed)
        self._content = [i.strip() for i in temp if i.strip()]
        log(self._logfile, 'Done getting the contents from the request page')
        return self._content

    # Utilities dealing with dates
    def replace_months(self, date):
        """This function replaces the names of months in the strings"""
        log(self._logfile, 'Replacing months')
        for i, j in Page.nldate.items():
            date = date.replace(i, j)
        log(self._logfile, 'Don replacing months')
        return date

    def filter_date(self, line):
        log(self._logfile, 'Filtering data for %s' % line)
        pattern = r'(\d{1,2} (%s) \d{4} \d{2}:\d{2})' % ('|'.join(Page.nldate))
        return re.findall(pattern, line)  # This method also accounts for hours & minutes

    def format_date(self, date):
        """This function formats a date in the nlwiki format. The returned date only contains information on the day,
        month, and year the request was passed """
        assert isinstance(date, str), "Please pass a string as the argument of format_date!"
        d = dt.datetime.strptime(self.replace_months(date),
                                 '%d %m %Y %H:%M')  # this is the object that can actually do the job for us

        # Return time, set back to UTC
        # To avoid exceptions around transition, assume "winter time" (conservative approach)
        return dt.datetime(year=d.year,
                           month=d.month,
                           day=d.day,
                           hour=d.hour,
                           minute=d.minute) - Page.timezone.utcoffset(d,
                                                                      is_dst=False)

    def get_date_for_lines(self, lines):
        """This function will return the most recent contribution date that corresponds with a given request."""
        for k in lines[::-1]:  # Run the inverse
            try:
                date_temp = self.filter_date(k)[0][0]  # Get the date on that line (using Regex)
                return self.format_date(date_temp)  # Convert the found date into an actual DateTime
            except IndexError:  # It's easier to ask for forgiveness, as this sin can be forgiven easily.
                date_temp = None
        # No date was found, use an emergency procedure
        return dt.datetime.today()

    # Utilities for actual processing of the page's content
    def split_page(self, level=None):
        """
        Method will search an entire page, identify the headers and split the page wherever needed
        """
        # If there is no manual override, take the header level passed in the configuration
        if level is None or not isinstance(level, int):
            level = self._level

        # Prepare pattern for regex search
        pattern = "={2,%d}\s*[^=]+\s*={2,%d}" % (level - 1, level - 1)

        # If the page content is not yet loaded, load it
        if not self._content:
            self.get_page_content()

        # Identify all sections in the system (level = the level of headers that should be archived)
        # The sections are the basis for the archiving
        # Based on these sections, we can do the archiving
        headers = {'$START': 0,
                   '$END': len(self._content)}  # Dictionary title: line number
        for i, line in enumerate(self._content):
            if re.match(pattern, line) is not None:  # We found a header!
                headers[line.replace('=', '').strip()] = i

        # Once headers are found, locate the headers that we need
        self._startrule, self._endrule = headers[self._startsection], headers[self._endsection]

        # Time to make the actual split
        # Previous versions would store preamble separately, we don't do that here
        # Saves memory (we will instead rely on properties)
        self._hot = self._content[self._startrule:self._endrule]

    # Properties to deal with the parts of the page that we don't need
    @property
    def pre(self):
        if self._startrule is None:
            raise ValueError('We still need to split the page!')
        if self._startrule == 0:
            return []
        return self._content[:self._startrule]

    @property
    def post(self):
        if self._endrule is None:
            raise ValueError('We still need to split the page!')
        if self._endsection == '$END':
            return []
        return self._content[self._endrule:]

    # Where the actual magic happens
    def identify_old_discussions(self):
        if not self._hot:
            self.split_page()

        # First step: prepare regex
        pattern = "={%d}\s*[^=]+\s*={%d}" % (self._level, self._level)

        # Second step: find the headers & store their locations
        suited = [i for i, line in enumerate(self._hot) if re.match(pattern, line)]
        suited.append(len(self._hot))  # Make sure the last request is also processed

        # Third step: check which requests can be thrown out
        # Note: all times are reported in UTC, no need for additional corrections
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=self._passed_dates)
        old = {}
        for start, end in zip(suited[:-1], suited[1:]):
            last_comment = self.get_date_for_lines(self._hot[start:end])
            if last_comment < cutoff:
                print(last_comment, cutoff, start)
                old[(start, end)] = last_comment
        self._delete += sorted(old.keys())
        return old  # Return the list of requests to be removed

    # Method to grab the text to add to the archive
    def get_text_for_archive(self, checked=False, presort=False):
        if not self._delete and checked is False:
            self.identify_old_discussions()  # Previous functions were not executed

        if presort is False:
            self._delete.sort()
        output_text = '\n'

        # Oldest request first please (oldest = first listed on the request page)
        for start, end in self._delete:
            output_text += '\n'.join(self._hot[start:end])
            output_text += '\n'
            if self._hot[end - 1] and end != self._delete[-1][-1]:
                output_text += '\n'  # Make sure a blank line is inserted after each request
        return output_text

    # Get the new text for the original page
    def get_text_for_page(self, checked=False, presort=False):
        if not self._delete and checked is False:
            self.identify_old_discussions()

        if presort is False:
            self._delete.sort()

        # Here, we need to bother about the oldest request first
        temp = self._hot.copy()
        for start, end in self._delete[::-1]:
            del temp[start:end]

        # Assemble the full text
        output_text = ''
        output_text += '\n'.join(self.pre)
        output_text += '\n'
        output_text += '\n'.join(temp)
        del temp  # No longer needed in memory
        output_text += '\n'
        output_text += '\n'.join(self.post)
        return output_text

    # The core of the algorithm: the update method
    def update(self, logonly=False, testing=False):
        # Testing = True has been set as default value for the initial testing phase!

        # First check: testing True ==> set bot into testing mode
        if testing is True:
            self.testing = True

        # Get the page's content and perform all preparation steps
        self.get_page_content()
        self.split_page()

        # Identify the old discussions
        self.identify_old_discussions()

        # And do the updating
        if self._delete:  # Don't do anything if there are no requests to be archived
            archived_sections = len(self._delete)  # For logging purposes
            if archived_sections == 1:
                summary_from = '1 verzoek verplaatst naar [[%s|archief]]' % (self.archive_target)
                summary_dest = '1 verzoek verplaatst van [[%s|verzoekpagina]]' % (self.name)
            else:
                summary_from = '%d verzoeken verplaatst naar [[%s|archief]]' % (archived_sections,
                                                                                self.archive_target)
                summary_dest = '%d verzoeken verplaatst van [[%s|verzoekpagina]]' % (archived_sections,
                                                                                     self.name)
            print(summary_from, summary_dest)
            # Time to do some updating
            self._delete.sort()
            new_original_text = self.get_text_for_page(presort=True)
            add_archive = self.get_text_for_archive(presort=True)
            # If testing is enabled, we should not be posting anything to the wiki!
            if self.testing is True:
                with open(gs.test_output, 'w', encoding='utf-8') as test_output:
                    test_output.write(new_original_text)
                with open(gs.test_archive, 'w', encoding='utf-8') as test_archive:
                    test_archive.write(add_archive)
                print('BOT RAN IN TEST MODE!')
            else:
                # Step 1: feed the archive
                append_dic = {'action': 'edit',
                            'title': self.archive_target,
                            'appendtext': add_archive,
                            'summary': summary_dest,
                            'bot': True,
                            'nocreate': True,
                            'starttimestamp': self._timestamp}
                # Step 2: write the new text to the request page
                edit_dic = {'action': 'edit',
                            'pageid': self.id,
                            'text': new_original_text,
                            'summary': summary_from,
                            'bot': True,
                            'nocreate': True,
                            'basetimestamp': self._timestamp}
                if logonly is False:
                    self.bot.post(append_dic)
                    self.bot.post(edit_dic)
                elif logonly is True:
                    print('LOGONLY!')
                    print(append_dic)
                    print('\n')
                    print(edit_dic)
        else:
            print('Nothing to be done!')

    def __call__(self, logonly=False):
        return self.update(logonly=logonly)


# Testing
jef = Page('Wikipedia:Verzoekpagina voor moderatoren/Sokpoppen',
           'Wikipedia:Verzoekpagina voor moderatoren/Sokpoppen/Archief/2024')
jef.testing = False
jef()
