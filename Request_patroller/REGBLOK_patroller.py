"""
A Python script to patrol the Dutch Wikipedia's REGBLOK page.

@author: Daniuu
@date: 23 August 2024
"""

import re
import Core as c
import REGBLOK_approved_reasons as rar
from IPBLOK_patrol import IPBLOK
from IPBLOK_patrol import Request as ParentRequest


def has_lock_message(request_lines, request):
    """
    Checks whether a lock message is present in the request.
    """
    if request.locked is True:
        if not(any(Request.lockstring in i for i in request_lines)):
            return False
    return True


class REGBLOK(IPBLOK):  # There is quite some resemblance between IPblock and REGBLOK
    def __init__(self,
                 name = 'Wikipedia:Verzoekpagina voor moderatoren/RegBlok',
                 testing = False):
        super().__init__(name, testing)
        self._logfile = 'REGBLOK_log.txt'

    # Override separate function from the common file
    # REGBLOK is quite a special page, since it uses the 5 sysops option (separate header...)
    # Those requests require special treatment (unlike WP¨:VV & WP:IPBLOK)
    def separate(self):
        super().separate()
        # Extra step for REGBLOK specifically: the 5-sysops option should be sent to a different list
        # We don't want those requests to be processed with the rest of the regular queue
        # This is a bit of copy & paste
        inter = 'Nieuwe verzoeken ter beoordeling door meerdere moderatoren'
        t = [i.replace('=', '').strip() for i in self._queue]  # Generate a list with all the levels neutralized
        try:
            ih = t.index(inter)
        except ValueError:
            # This indicates that something wrong was added
            print('Watch out! The required headers were not found in the list')
            return None
        self._inter, self._queue = self._queue[ih:], self._queue[:ih]  # Complete the effort
        c.log(self._logfile, 'Done separating!, stage 2')
        return self._queue  # Same behavior as the parent function (for the queue at least)

    def prepare_regex(self):
        user_string = '[^\}]+'
        templates = ('lg', 'lgcw', 'linkgebruiker', 'lgx')
        regex_template = r'\{\{(%s)\s*\|\s*' % (
            '|'.join(templates)).lower()  # A pattern that makes handling the templates easier
        self.regex = ('(%s(%s))' % (regex_template, user_string))
        c.log(self._logfile, 'Regex prepared for REGBLOK')
        return self.regex  # Searches will be case-insentive here

    def check_line(self,
                   line,
                   forreq=True):
        """
        This function checks whether an IP is on the line, and returns those. If forreq is False, the requests are
        not generated explicitly
        """
        if 'Naam account' in line:  # Stupid way of avoiding the explanation, but it works :)
            return False
        if self.regex is None:
            self.prepare_regex()  # The regex has not yet been initialized properly
        # Following issue of 2 February 2024: Don't list lines with a donetemp in there!
        # c.log(self._logfile, 'Scanning for requests: %s'%line)
        if any(('{{%s}}'%i in line.lower() for i in super().donetemp)) or any(('{{%s}}'%i in line.lower() for i in super().donetemp)):
            return [] if forreq is True else False

        k = re.findall(self.regex, line, re.IGNORECASE)  # Make it upper, so the regex can do it's job as it should do
        if not k:
            return None  # Returns None, indicating that the list of matches is empty
        if isinstance(k[0], tuple):
            k = [i[0] for i in k]  # Get the longest matching sequence
        c.log(self._logfile, 'Done scanning line %s'%line)
        if forreq is True:
            return [Request(i) for i in k if '{{' in i and '|' in i]  # No need to test for IP match here...
        return bool(k)

    # Override needed to deal with lock messages
    def filter_queue(self, ran=False):
        super().filter_queue()
        if ran is False:  # Lock messages are just appended to the queue, so we need to add them manually
            if self.check_lock_messages() is True:
                return self.filter_queue(True)
        return self.requests  # To mimic the behaviour of the parent function

    def check_removal(self, *args, **kwargs):
        return 0  # REGBLOK entries should never be deleted!

    # Additional feature: leave a remark whenever a user has been locked
    def check_lock_messages(self):
        insert = []
        if not self._queue:
            self.separate()
        for i, j in self.requests.items():
            if not isinstance(i, str):  # Ignore flagged requests
                if i.locked and not has_lock_message(self._queue[j[0]: j[1]], i):
                    insert.append((j[1], f'{Request.lockstring} ~~~~'))
        # And now add the lock messages
        insert.sort(reverse=True)
        for i, j in insert:
            self._queue.insert(i, f'{c.get_prefix(self._queue[i - 1])}{j}')
        return bool(insert)


class Request(ParentRequest):

    account_forbidden = ('#',
                         '<',
                         '>',
                         '[',
                         ']',
                         '{',
                         '}')  # Forbidden characters in account names, minus | (used in templates)

    lockstring = '{{Vergrendeld}}'

    def __init__(self, line):
        super().__init__(line)
        self.locked = False  # For safety
        self.check_locked()  # Check if a given user was locked (special treat for accounts)

    def process(self, origin, **kwargs):
        # Additional part for accounts: strip out forbidden characters
        assert isinstance(origin, str), 'Request.process can only handle strings!'
        for i in Request.account_forbidden:  # Auxiliary tool to get rid of some chars that might get caught by regex
            if i in origin:
                origin = origin.replace(i, '')  # Remove this forbidden character
        return super().process(origin, False)

    def get_blocks(self,
                   property_l='bkusers',
                   property_g='bgtargets'):
        super().get_blocks(property_l, property_g)  # Pass our keywords directly

    # Add-on for accounts: is the account globally locked
    def check_locked(self):
        payload = {'action': 'query',
                   'meta': 'globaluserinfo',
                   'guiuser': self.target}
        out = Request.bot.get(payload)['query']['globaluserinfo']
        self.locked = 'locked' in out
        return self.locked

    def process_blocks(self, target_name='target'):
        super().process_blocks(target_name)

    def verify_reason(self):
        """
        Additional method, dedicated to the handling of block requests for registered users.
        These requests should only be handled if the user is blocked for a very specific reason.

        Output: bool, indicating whether the summary matches one of the presets
        """
        if self.main is not None and 'reason' in self.main:
            # Verify whether the summary matches one of the pre-defined criteria
            low = self.main['reason'].lower()
            for i in rar.regblok_contains:
                if i in low:
                    return True
            for i in rar.regblok_matches:
                if i == low:
                    return True
        return False

    def __bool__(self):
        # Be aware chap, these requests can only be handled if the block was performed for a very specifiic set of
        # reasons
        return super().__bool__() and self.verify_reason()


if __name__ == '__main__':
    a = REGBLOK()
    a(logonly=True)  # We don't want the script to actually write to the wiki YET
