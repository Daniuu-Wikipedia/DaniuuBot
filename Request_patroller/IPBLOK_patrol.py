# -*- coding: utf-8 -*-
"""
Created on Sun Jun 20 12:21:36 2021

@author: Daniuu

This script is designed to automatically patrol the Dutch Wikipedia IPBLOK-request page
Please note: this script is still in an experimental phase, 
"""

import Core as c
import Request_patroller_common as com
import datetime as dt
import re
import Bot_settings as bs


class IPBLOK(com.Page):
    "This class contains the main content for the page related operations"

    def __init__(self,
                 testing=False):
        # Argument "testing" can be set to True if the bot needs to be tested
        super().__init__('Wikipedia:Verzoekpagina voor moderatoren/IPBlok', testing)
        self.regex = None  # Store the default regex pattern here
        self.prepare_regex()
        self._logfile = 'IPBLOK_log.txt'
        c.clear_log_file(self._logfile)
        c.log(self._logfile, 'Initialization done')

    def separate(self):
        return super().separate('Nieuwe verzoeken', 'Afgehandelde verzoeken')

    def prepare_regex(self):
        "Prepare the regex-pattern for future searches"
        # Prepare the regex pattern
        ip4 = r'(\d{1,3}\.){3}\d{1,3}'  # Regex pattern used to detect ip4-adresses (and ranges)
        ip6 = r'([\dABCDEF]{1,4}:){4,7}([\dABCDEF:]{1,4})+?'  # Regex pattern used to detect ip4-adresses (and ranges)
        templates = ('lg', 'lgipcw', 'lgcw', 'linkgebruiker', 'Link IP-gebruiker cross-wiki', 'lgx')
        regex_template = r'\{\{(%s)\s*\|\s*' % (
            '|'.join(templates)).upper()  # A pattern that makes handling the templates easier
        self.regex = ('(%s(%s|%s))' % (regex_template, ip4, ip6))
        c.log(self._logfile, 'Regex prepared for IPBLOK')
        return self.regex  # Convert everything to capitals for consistency

    def check_line(self, line, forreq=True):
        "This function checks whether an IP is on the line, and returns those. If forreq is False, the requests are not generated explicitly"
        if self.regex is None:
            self.prepare_regex()  # The regex has not yet been initialized properly
        # Following issue of 2 February 2024: Don't list lines with a donetemp in there!
        c.log(self._logfile, 'Scanning for requests: %s'%line)
        if any(('{{%s}}'%i in line.lower() for i in super().donetemp)) or any(('{{%s}}'%i in line.lower() for i in super().donetemp)):
            return [] if forreq is True else False

        k = re.findall(self.regex, line.upper())  # Make it upper, so the regex can do it's job as it should do
        if not k:
            return None  # Returns None, indicating that the list of matches is empty
        if isinstance(k[0], tuple):
            k = [i[0] for i in k]  # Get the longest matching sequence
        c.log(self._logfile, 'Done scanning line %s'%line)
        if forreq is True:
            return [Request(i) for i in k if ('{{' in i and '|' in i and (i.count('.') == 3 or i.count(
                ':') >= 4))]  # Only return the matches that are real calls to the template
        return bool(k)

    def filter_queue(self):
        """This function will filter the required requests out of the queue."""
        # Additional logging for Toolforge
        c.log(self._logfile, 'Starting to go through the queue of existing requests')
        if not self._queue:  # This means that the split was not yet done
            self.separate()  # If the split was not yet done, then do the split, is it so difficult?

        # check what lines are containing requests (and are flagged)
        reqs, flagged = [], []  # List with line numbers where requests were found and where indication of flagged templates were found

        # Adjustment 20240626 - also detect headers
        header_on_line = False

        for i, j in enumerate(self._queue[1:]):
            if self.header_on_line(j):
                header_on_line = True
            else:
                z = self.check_line(j)  # Check whether any requests are on this line
                if z:  # We found requests on the line - this should be stored
                    if header_on_line is False:
                        reqs.append(
                            (i + 1, z))  # +1 cause we left out the first element of the queue - make the MultiRequest later
                    elif header_on_line is True:
                        reqs.append(
                            (i, z))  # We actually want to append the previous line (code relies on people dropping their request on the first line and not after writing some novel...)
                elif any(('{{' + k + '}}' in j for k in c.Page.donetemp)):  # check whether anything got marked
                    flagged.append(
                        i + 1)  # Add this line to the list of lines where a template with a nice little flag is present

        # Cancel the loop, continue with putting the requests in a well structured format
        if not reqs:
            return self.requests  # No additional requests found, return this dictionary
        reqs.append((len(self._queue), None))  # Add a placeholder that makes life easier
        for i, j in zip(reqs[:-1], reqs[1:]):
            req_flagged = False  # Reset this to False when starting a new iteration, will be used to detect a flagged request
            # i is the line where a request is present, j where the next request starts (or where the queue ends)
            if any((k in flagged for k in range(i[0], j[0]))):
                self.requests['flagged'] = self.requests.get('flagged', []) + [
                    (i[0], j[0])]  # Largely the same af for the revdel patrol
                req_flagged = True  # Just adding this variable for further reference
            on_line = MultiRequest(i[1])  # The requests that can be found on this line
            if on_line in self.requests:  # This one was found before
                self.requests[on_line] = (self.requests[on_line][0], j[0])
                if req_flagged is True:
                    self.requests['flagged'] = self.requests.get('flagged', []) + [(self.requests[on_line][0], j[0])]
            else:
                self.requests[on_line] = (i[0], j[0])  # Store this as a request in all cases
        c.log(self._logfile, 'Done filtering the queue')
        return self.requests  # Return the updated dictionary

    def check_requests(self):
        "This function will mark the done requests as done (and is called by the update method)"
        if not self._queue:
            self.separate()
        self.check_queue_done()  # First run this one to check whether the requests in the queue are done or not
        # Go through all the requests (and check whether they were already manually flagged or not)
        flagged = self.requests.get('flagged',
                                    [])  # Get list of flagged requests, and return an empty list if there are None
        todel = []  # A list of indices that should be removed from the queue
        for i, j in self.requests.items():
            if not isinstance(i,
                              str):  # Skip strings, they are just some weird construction to make things easier or so
                if i or j in flagged:  # Obviously, only do this once the request is completed or manually flagged
                    self._done += self._queue[j[0]:j[1]]  # Transfer the requests to the list of done ones
                    todel.append(j)  # Add to the list of indices that should be deleted later on
                    if j not in flagged:  # The request has not yet been flagged manually, fix this
                        pre = self._queue[j[1] - 1].split()[0]
                        if "*" in pre:
                            prefix = '*' * (pre.count('*') + 1)
                        else:
                            prefix = ':'
                        self._done.append(prefix + i.done_string())
        return self.clear_lines(self._queue, todel)

    def check_removal(self):
        """Function determines which requests can be deleted."""
        # Previously, the settings controlling the delay in removing the request were implemented as keyword arguments
        # Settings have been fully moved to the Bot_settings.py file
        # The move was done to centralize all this kind of settings
        days, hours = bs.ipblok_removal_days, bs.ipblok_removal_hours
        c.log(self._logfile, 'Checking which requests could be removed')
        # Browse all lines of the 'done queue'
        if not self._done:
            self.separate()  # First generate the queue, much better

        # Adjustment 20240626 - also account for headers above the requests
        # My apologies to the Python gods of brief code - had to replace the previously-used list comprehension
        # Note: this code is also used in the revdel patroller!
        reqlines, header_detected = [], False
        for i, j in enumerate(self._done):
            if self.header_on_line(j):
                header_detected = True
                reqlines.append(i)
            elif self.check_line(j, forreq=False):
                if header_detected is False:
                    reqlines.append(i)
                else:
                    header_detected = False  # Skip the line & merge the request with the previous one
        reqlines.append(len(self._done))
        to_del = []  # List of tuples with requests that should be removed from Done
        for i, j in zip(reqlines[:-1], reqlines[1:]):
            try:
                request_date = self.get_date_for_lines(self._done[i:j])
                if isinstance(request_date, dt.datetime):
                    # A valid date has been found, check whether we can now delete
                    if request_date + dt.timedelta(days=days, hours=hours) <= dt.datetime.utcnow():
                        to_del.append((i, j))
            except IndexError:  # This popped up once because somebody did not take the time to sign off the request
                self._done.insert(j,
                                  '**{{opm}}: Dit verzoek bevat mogelijks geen correcte datumstempel. Als deze melding klopt, kan u de datum toevoegen via {{tl|afzx}} en melding terug verwijderen. ~~~~')
        c.log(self._logfile, 'Done checking which requests could be removed')
        return self.clear_lines(self._done, to_del)


class Request(com.GenReq):
    bot = c.NlBot()  # We are now testing
    now = dt.datetime.utcnow()  # Store the current time to check whether

    def __init__(self, ip):
        super().__init__(ip, (str,))
        self.blocks, self.gb = [], []
        self.main = None  # This is where we will store the block that is primarily affecting the person here

    def process(self, origin):
        if '|' not in origin:
            return origin.strip().upper().strip()
        return origin.split('|')[1].strip().upper()  # Always convert to capitals

    def get_blocks(self):
        "This function will check whether the user was blocked or not"
        dic = {'action': 'query',
               'list': 'blocks|globalblocks',
               'bkip': self.target,
               'bgip': self.target,
               'bklimit': 500,
               'bglimit': 500,
               'bkprop': 'user|by|timestamp|expiry',
               'bgprop': 'address|by|timestamp|expiry'}
        output = Request.bot.get(dic)['query']
        self.blocks, self.gb = output['blocks'], output['globalblocks']
        self.process_blocks()  # Automatically call this function too

    def process_blocks(self):
        "This function will ensure the blocks are properly formatted"
        # Begin with the global blocks
        for i in self.gb:
            i['global'] = True  # Just adding this for further use in the API
            i['user'] = i['address']  # Something to make it compatible with the normal blocks
            start, end = i['timestamp'], i['expiry']  # Some date formatting
            if not isinstance(start, dt.datetime):
                i['timestamp'] = self.convert_api_date(start)
            if not isinstance(end, dt.datetime):
                i['expiry'] = self.convert_api_date(end)
                end = i['expiry']

        for i in self.blocks:
            i['global'] = False  # Someone is only locally blocked, just add False in the global header
            start, end = i['timestamp'], i['expiry']  # Some date formatting
            if not isinstance(start, dt.datetime):
                i['timestamp'] = self.convert_api_date(start)
            if not isinstance(end, dt.datetime):
                i['expiry'] = self.convert_api_date(end)
                end = i['expiry']

    def check_blocked(self):  # For the test phase
        "This function will check whether a given IP is blocked. A 10 minute delay prior to flagging is used"
        # Previously, the setting controlling the delay in processing the request was implemented as keyword arguments
        # Settings have been fully moved to the Bot_settings.py file
        # The move was done to centralize all this kind of settings
        # The "delay" setting gives the blocking sysop the chance to make a statement of their own
        delay = bs.ipblok_processing_delay_minutes
        # The "expiry" setting prevents the bot from flagging blocks that were made more than the given time ago
        expiry = bs.ipblok_block_expiry
        self.get_blocks()  # First, get the blocks from the API
        self.blocks.sort(key=lambda i: i['timestamp'], reverse=True)  # Sort, most recent blocks first
        too_old = Request.now - expiry  # Don't handle blocks older than this delay
        for i in self.blocks:
            if too_old <= i['timestamp'] + dt.timedelta(
                    minutes=delay) <= Request.now:  # This gives the blocking sysop the time to place a block
                if i['expiry'] > Request.now:  # Verify that the block did not yet expire
                    self.main = i
                    return self.main

        # Now check the global blocks
        self.gb.sort(key=lambda i: i['timestamp'], reverse=True)
        for i in self.gb:
            if i['timestamp'] + dt.timedelta(
                    minutes=delay) <= Request.now:  # This gives the blocking sysop the time to place a block
                if i['expiry'] > Request.now:  # Verify that the block did not yet expire
                    self.main = i
                    return self.main

    def __bool__(self):
        "This function will convert the entire function into a boolean"
        if self.main is None:
            self.check_blocked()
        return self.main is not None

    def get_and_check_block(self):
        "This function will combine some of the functions above"
        self.get_blocks()
        self.check_blocked()

    def get_name(self):
        "This method will return the name of the sysop (or steward) who administered the block"
        if self:
            return 'steward ' * self.main['global'] + self.main['by']

    def done_string(self):
        "This function returns a string that indicates that the user was blocked"
        if self:
            return '{{done}} - %s is voor %s geblokkeerd door %s. Dank voor de melding. ~~~~' % (
            self.blocked(), self.duration(), self.get_name())

    def blocked(self):
        "Get which IP's are blocked."
        if self:
            return self.main['user']  # Kijk na welke gebruiker er is geblokkeerd

    def short_string(self):
        "Will return a short string, explaining whether a block was administered"
        if self:
            return '%s is voor %s geblokkeerd door %s' % (self.blocked(), self.duration(), self.get_name())

    def duration(self):
        "Get how long the IP has been blocked"
        if not self:
            return None  # Make sure this special case cannot accidentally leak
        dur = self.main['expiry'] - self.main['timestamp']
        # Divide the duration into smaller intervals
        years, months, weeks = dur // dt.timedelta(days=365), dur // dt.timedelta(days=28), dur // dt.timedelta(days=7)
        if years > 1000:
            return 'onbepaalde tijd'  # An IP was indeffed
        if years:
            return '%d jaar' % years
        if months:
            return '%d maand(en)' % months
        if weeks:
            return '%d we(e)k(en)' % weeks
        days, hours = dur // dt.timedelta(hours=24), dur // dt.timedelta(hours=1)
        if days:
            return '%d dag(en)' % days
        return '%d uur' % hours

    def __call__(self):
        "This function is used by MultiRequest, and handles the entire request at once"
        if not self:  # The request has not yet been completed
            self.check_blocked()
        return self.short_string()  # Especially handy when this has to be combined with MultiRequest


class MultiRequest(com.GenMulti):
    def check_done(self):
        "Checks whether all requests were already handled or not."
        self.done = all((bool(i) for i in self.targets))
        return self.done

    def __str__(self):
        return str(self.targets)

    def __eq__(self, other):
        "This function is required to test equality"
        return sorted(self.targets) == sorted(other.targets)

    def __hash__(self):
        return tuple(self.targets).__hash__()

    def done_string(self):
        "This will generate a string that indicates whether all listed IP's are blocked"
        if not self:
            return None  # Just stop this shit
        subs = [i.short_string() for i in self.targets]
        return '{{d}} - %s %s %s. Dank voor de melding. ~~~~' % (', '.join(subs[:-1]),
                                                                 ' & ' * (len(subs) > 1),
                                                                 subs[
                                                                     -1])  # Generate the string that indicates that all blocks were administered


class Test(IPBLOK):
    "The function that should be put to testwiki"

    def __init__(self):
        super().__init__()
        self.name = 'Verzoekpagina'
        self.bot = c.TestBot()

    def format_date(self, date):
        "Overrides this with the conventions for testwiki"
        assert isinstance(date, str), "Please pass a string as the argument of format_nldate!"
        for k, l in com.Page.testdate.items():
            date = date.replace(k, l)
        for k, l in com.Page.nldate.items():
            date = date.replace(k, l)
        return dt.datetime.strptime(date, '%d %m %Y')  # this is the object that can actually do the job for us


# Execution code
if __name__ == '__main__':
    s = IPBLOK()
    s()  # Pass True to place this bot into log-only
