"""
Archive bot

This bot was developed following a request by Akoopal (for an archive bot that could deal with headers & subheaders)
@author: Daniuu

"""

# Main imports
import Core as c

from toolforge import set_user_agent  # To set our user agent to something nicer
import datetime as dt  # Import support for dates and times
import re
import os
import pytz  # Timezone management
import nldate as nld
import General_settings as gs
import Date_utils as du

# Before taking any actions, change the UA to something nicer
set_user_agent('Daniuu-Bot')


# Functionality to allow logging
def clear_log_file(file):
    with open(file, 'w', encoding='utf8') as blankfile:
        blankfile.write('%s\n' % (dt.datetime.utcnow()))


def log(file, text):
    with open(file, 'a', encoding='utf8') as logfile:
        logfile.write(text.rstrip() + '\n')


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

    timezone = pytz.timezone('Europe/Amsterdam')  # nlwiki uses Amsterdam time

    bot = c.NlBot()  # Tijdelijk op de betawiki werken (testdoeleinden)

    def __init__(self,
                 configuration_dict,  # Read configuration from a JSON file
                 dir=None,
                 testing=False):
        if dir is not None and os.path.exists(dir):
            os.chdir(dir)
        # Names of relevant pages
        self.archive_target = configuration_dict['archive_target']  # New version: this will be parameterized
        self.name = configuration_dict['name']

        # Store page content
        self._content = []
        # Different parts of the page...
        self._hot = []
        self.requests = {}  # This is a list of requests that are in the queue

        # The Bot that will perform the actions
        self.bot = Page.bot  # One bot for all pages should be fine
        self.id = None

        # File for logging
        self._logfile = 'Log.txt'
        # Code implemented solely for testing purposes
        # A boolean value will be used to check whether we are testing the bot or fully operational
        # The boolean is called by the functions updating the final page
        # Furthermore, the boolean is checked by the function that gets the page content
        # If set to True, the Bot will operate in its testing mode!
        self._testing = testing
        self._use_real_page = True  # Default for testing

        # Timestamp to check for edit conflicts
        self._timestamp = None

        # Properties to be read from the bot's settings
        # These include the level of headers to be archived & sections that need archiving
        # AT PRESENT: test values have been hardcoded!
        self._startsection = configuration_dict['startsection']
        self._endsection = configuration_dict['endsection']
        self._level = configuration_dict['level']
        self._passed_dates = configuration_dict['passed_dates']

        # 20240722 - enable archiving to a specific section in the archive
        self.archive_target_section = configuration_dict.get('archive_target_section')

        # Additional safeguard: is an empty string is passed: swap to None
        if isinstance(self.archive_target_section, str) and not self.archive_target_section:
            self.archive_target_section = None

        # 20240722 - allow some archivers to create new sections in the archive
        # This will only be allowed if the bot is configured accordingly

        self._allow_new_sections = configuration_dict.get('allow_new_sections', False) == "True"  # Default to False

        # Store handy indices (improve memory-efficiency)
        self._startrule, self._endrule = None, None

        # Store indices that can be deleted
        self._delete = {}  # Dictionary, (rule start, rule end): archive name as items

        # Store list of faulty pages that should ignored until resolution by the developer
        with open(gs.abort_file, 'r', encoding='utf8') as abortfile:
            self.__faulty_pages = {i.strip() for i in abortfile}
        if self.__faulty_pages:
            print(self.__faulty_pages)  # 20240722 - log if a page is skipped due to a fault

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

    # To test with the real page & not a dummy
    @property
    def use_real(self):
        return self._use_real_page

    @use_real.setter
    def use_real(self, use_real):
        if isinstance(use_real, bool):
            self._use_real_page = use_real

    @use_real.deleter
    def use_real(self):
        self._use_real_page = False

    # 20240722 - Get the id of the section to write to
    def calculate_archive_section(self, archive_title, section=None):
        if self.archive_target_section is None:
            return None
        # Step 1: Parse the target archive page and parse the sections
        pdic = {'action': 'parse',
                'page': archive_title,
                'prop': 'sections'}
        parsed = Page.bot.get(pdic)['parse']['sections']

        # 20240722 - extension to allow writing to custom sections & making new sections
        if section is None:
            section = self.archive_target_section
        for i in parsed:
            if i['line'] == section and int(i['level']) == (self._level - 1):
                return int(i['number'])  # Abort run (we found the desired section)

        # 20240722 - allow creation of new sections if required
        if self._allow_new_sections is not True:
            raise ValueError('I could not find the section! You did not allow to create a new one: %s' % section)
        return max(
            (i['number'] for i in parsed)), True  # If the section is not yet there, just append it (BE CAREFUL AT
        # STARTUP)

    # Utility to get the content of the page
    def get_page_content(self):
        """This function will get the last revision of the request page"""
        log(self._logfile, 'Starting to parse the request page')
        if self._testing is False or self._use_real_page is True:
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
        # 20240712 - add safeguard to stop bot from misbehaving
        for line in temp:
            if any((i.lower() in line for i in gs.abort_strings)):
                # If this code is called, abort all running and don't make any further requests
                print('\nBOT FORCIBLY TERMINATED DUE TO STOP STRINGS\n')
                raise c.Aborted()  # Make sure the program stops here
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

    def get_date_for_lines(self, lines, reverse=True):
        """This function will return the most recent contribution date that corresponds with a given request."""
        for k in (lines[::-1] if reverse is True else lines):  # Run the inverse
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
        pattern = "={1,%d}\s*[^=]+\s*={1,%d}" % (level - 1, level - 1)

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
        suited = [i for i, line in enumerate(self._hot) if re.match(pattern,
                                                                    line) and '=' * (self._level + 1) not in line]
        suited.append(len(self._hot))  # Make sure the last request is also processed

        # Third step: check which requests can be thrown out
        # Note: all times are reported in UTC, no need for additional corrections
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=self._passed_dates)
        old = {}
        for start, end in zip(suited[:-1], suited[1:]):
            last_comment = self.get_date_for_lines(self._hot[start:end])
            if last_comment < cutoff:
                reqdate = self.get_date_for_lines(self._hot[start:end], reverse=False)  # Date of actual request
                dest = du.format_archive_for_date(reqdate, self.archive_target)
                # 20240722 - changes to enable writing to custom sections & creation of new section
                dsec = du.format_archive_for_date(reqdate, self.archive_target_section)
                self._delete[(start, end)] = (dest, dsec)
                del reqdate  # Just clearing a bit of memory & avoiding trouble
        return old  # Return the list of requests to be removed

    # Method to grab the text to add to the archive
    def get_text_for_archive(self, name, checked=False):
        if not self._delete and checked is False:
            self.identify_old_discussions()  # Previous functions were not executed

        output_text = '\n'

        # Oldest request first please (oldest = first listed on the request page)
        for start, end in sorted(self._delete.keys()):
            if self._delete[(start, end)] == name:
                output_text += '\n'.join(self._hot[start:end])
                output_text += '\n'
                if self._hot[end - 1]:
                    output_text += '\n'  # Make sure a blank line is inserted after each request

        # Strip the last entry of the last line to be added
        if not output_text[-1]:
            del output_text[-1]
        return output_text

    # Get the new text for the original page
    def get_text_for_page(self, checked=False, presort=False):
        if not self._delete and checked is False:
            self.identify_old_discussions()

        # Here, we need to bother about the oldest request first
        temp = self._hot.copy()
        for start, end in sorted(self._delete.keys(), reverse=True):
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

        # Second check: page has not given any faults up till now
        if self.name in self.__faulty_pages:
            print('Ignored', self.name)
            return None  # Abort the method here, the developer must fix the issues first

        # Get the page's content and perform all preparation steps
        self.get_page_content()
        self.split_page()

        # Identify the old discussions
        self.identify_old_discussions()

        # And do the updating
        if self._delete:  # Don't do anything if there are no requests to be archived
            # Collect the names of all archives to which requests will be written
            archives = sorted(set(self._delete.values()))
            for a in archives:
                archived_sections = len([1 for j in self._delete.values() if j == a])  # For edit summary
                if archived_sections == 1:
                    summary_dest = '1 verzoek verplaatst van [[%s|verzoekpagina]]' % self.name
                else:
                    summary_dest = '%d verzoeken verplaatst van [[%s|verzoekpagina]]' % (archived_sections,
                                                                                         self.name)
                # Time to do some updating
                add_archive = self.get_text_for_archive(a)
                # If testing is enabled, we should not be posting anything to the wiki!
                if self.testing is True:
                    with open(gs.test_archive, 'w', encoding='utf-8') as test_archive:
                        test_archive.write('\n%s\n' % a[0])
                        test_archive.write(add_archive)
                    print('BOT RAN IN TEST MODE!')
                else:
                    # Step 1: feed the archive
                    append_dic = {'action': 'edit',
                                  'title': a[0],
                                  'appendtext': add_archive,
                                  'summary': summary_dest,
                                  'bot': True,
                                  'nocreate': True,
                                  'starttimestamp': self._timestamp}

                    # 20240722 - Extend code to write to individual sections
                    if self.archive_target_section is not None:
                        append_dic['section'] = self.calculate_archive_section(a[0], a[1])
                        # 20240722 - Extend code to write new sections if needed
                        if isinstance(append_dic['section'], tuple):
                            # No need to check for self._allow_new_sections (is done in self.calculate_archive_section
                            # We need to write a new section ==> make the change!
                            del append_dic['section']  # Just append at bottom of page
                            new_text = '\n'
                            new_text += '=' * (self._level - 1) + ' %s' % a[1] + '=' * (self._level - 1) + '\n'
                            new_text += append_dic['appendtext'].lstrip()
                            append_dic['appendtext'] = new_text

                    if logonly is False:
                        response = self.bot.post(append_dic)
                        if 'error' in response:
                            with open(gs.abort_file, 'a', encoding='utf-8') as abort_file:
                                abort_file.write(self.name + '\n')
                            raise c.API_Error(self.name)  # Abort all running for safety reasons
                        del response  # No need to keep it stored, avoid overlap from previous runs

                    elif logonly is True:
                        print('LOGONLY!')
                        print(append_dic)
                del add_archive  # To prevent weird accidents & edits
            # Do some summary preparation work
            total_archived = len(self._delete)
            if total_archived == 1:
                summary_from = '1 verzoek verplaatst naar archief'
            elif total_archived > 1:
                summary_from = '%d verzoeken verplaatst naar archief' % total_archived
            # Update the request page (we will only do that once all archives were written)
            new_original_text = self.get_text_for_page(presort=True)
            edit_dic = {'action': 'edit',
                        'title': self.name,
                        'text': new_original_text,
                        'summary': summary_from,
                        'bot': True,
                        'nocreate': True,
                        'basetimestamp': self._timestamp}
            if logonly is False and self.testing is False:
                response = self.bot.post(edit_dic)
                if 'error' in response:
                    with open(gs.abort_file, 'a', encoding='utf-8') as abort_file:
                        abort_file.write(self.name + '\n')
            elif logonly is True:
                print(edit_dic)
            elif self.testing is True:
                with open(gs.test_output, 'w', encoding='utf-8') as test_output:
                    test_output.write(new_original_text)
        else:
            print('Nothing to be done!')

    def __call__(self, logonly=False):
        return self.update(logonly=logonly)
