# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 18:10:03 2021

@author: Daniuu

This script provides some handy administrative tools, that could be used at the Dutch Wikipedia.
This bot uses designated OAuth keys (which are for obvious reasons stored in another file).
This script is designed to run under the account 'DaniuuBot'.
Some functions were specifically modified for this little tool.
"""

import re  # Regex
import datetime as dt  # Import support for dates and times
import Core as c


class Revdel(c.Page):
    def __init__(self):
        "Intializes the revdel bot."
        super().__init__('Wikipedia:Verzoekpagina voor moderatoren/Versies verbergen')

    def check_request_on_line(self, line,
                              pattern=r'(((direction=next|diff=(\d{1,9}|next|prev))\&)?oldid=\d{1,9}|permalink:\d{1,9}|\{\{diff\|\d{1,9}|speci(a|aa)l:diff(\/\d{1,9}){1,}|diff=\d{1,9})',
                              check=False, proc=False):
        "Checks whether the line passed as an argument contains any kind of requests"
        raw = re.findall(pattern, line.lower())  # this will unleash the regex on the poor little line
        if not raw:  # No pattern was found before
            raw = re.findall(r'\d{8,}', line.lower())  # Additional check to mark as a request
        z = []  # create a list to store all separate matches (and where we can leave out the empty matches if any)
        for i in raw:  # Go through all returned matches
            if isinstance(i, (tuple, list)):
                for j in i:  # check all separate elements of the tuple or list that was found
                    if j.strip():  # Check that j is not empty
                        z.append(j.strip())
            elif i:  # We found a string or so, can just be added if not empty
                z.append(i)
        if proc is True:
            z = [Request(i) for i in z if i and any((j.isdigit() for j in i))]
        if check is True:
            z += self.check_user_request(line)
        return z  # Returns the list with non-empty matches of the regex

    def check_user_request(self, line):
        "This function will check whether a request is made to hide all edits from a given user"
        # s = line.lower() #Prepare the pattern and remove all capitals
        out, pattern = [], r'((s|S)peci(a){1,2}l:((b|B)ijdragen|(c|C)ontributions)\/\S+)'  # Empty list for the output, pattern for the detection
        match = re.findall(pattern, line)
        for i in match:
            if isinstance(i, tuple):
                for j in i:
                    if len(j) > 15:  # Check whether Special:... is in the text (if not, it's fake news)
                        temp_ip = j.split('/')[1].strip()
                        if '|' in temp_ip:
                            temp_ip = temp_ip.split('|')[0].strip()
                        out.append(UserRequest(temp_ip))
        return out

    def separate(self):
        return super().separate('Nieuwe verzoeken', 'Afgehandelde verzoeken')

    def filter_queue(self):
        "This function will convert the strings in the queue to a requests that can be handled"
        if not self._queue:
            # This means that the split was not yet done
            self.separate()
        # First, check what lines contain requests
        reqs, flagged, jos = [], [], [None for _ in
                                      self._queue]  # Make a list with the lines containing requests, and where something got flagged
        for i, j in enumerate(self._queue[1:]):
            z = self.check_request_on_line(j, check=True,
                                           proc=True)  # Will also include IP's from now (check=True) keyword
            if z:
                reqs.append(i + 1)  # Just add i + 1 to the list of requests that were found
                jos[i + 1] = z  # Store it...
            elif any(('{{' + k + '}}' in j for k in c.Page.donetemp)):  # check whether anything got marked
                flagged.append(i + 1)

        # Now, do the processing of the lines
        if reqs:
            reqs.append(len(self._queue))  # Add this one, will make life easier in the remainder of the code
            for i, j in zip(reqs[:-1], reqs[1:]):
                # First, check whether the request has already been flagged
                if any((k in flagged for k in range(i, j))):
                    self.requests['flagged'] = self.requests.get('flagged', []) + [(i, j)]
                else:
                    self.requests.update({MultiRequest(jos[i]): (i, j)})
        return self.requests

    def check_requests(self):
        'This function will check whether all requests are done, and can move the request to the next part'
        self.check_queue_done()
        # First, process the requests that were marked manually
        sto = [(i, j, None) for i, j in
               self.requests.get('flagged', ())]  # Generate a list of tuples with 'None' as third element

        # Now, process the requestst that can be flagged automatically
        for i in self.requests:
            if not isinstance(i, str):  # These ones should be ignored (we can do the deletion first)
                if i:  # checks whether all requests have been handled
                    sto.append(self.requests[i] + (
                    i.check_person(),))  # Add the desired indices to the list that will be processed later

        # Begin processing the requests that are done or flagged
        sto.sort()  # Do in place sorting to make things easier
        for i, j, u in sto:  # Query the indices and add the request to the 'done' section
            self._done += self._queue[i:j]
            if u is not None:  # u is None indicates that the request was manually flagged
                pre = self._queue[j - 1].split()[0]
                if "*" in pre:
                    prefix = '*' * (pre.count('*') + 1)
                else:
                    prefix = ':'

                # Check the request itself and append the string to mark the request as done
                if u == 'DELETED':
                    self._done.append(
                        prefix + '{{opm}} - De pagina in kwestie werd reeds verwijderd. Dank voor de melding. ~~~~')
                else:
                    self._done.append(prefix + '{{d}} - ' + '%s Dank voor de melding. ~~~~' % u)
        for i, j, _ in sto[::-1]:  # Scan in reverse order - this will make the deletion sequence more logical
            del self._queue[i:j]
        return len(sto)  # Return the number of processed requests

    def check_removal(self, days=1, hours=4):
        "Function determines which requests can be deleted."
        # Browse all lines of the 'done queue'
        if not self._done:
            self.separate()  # First generate the queue, much better
        reqlines = [i for i, j in enumerate(self._done) if self.check_request_on_line(j, check=True)] + [
            len(self._done)]  # Manually add the length
        to_del = []  # List of tuples with requests that should be removed from Done
        for i, j in zip(reqlines[:-1], reqlines[1:]):
            request_date = self.get_date_for_lines(self._done[i:j])
            if isinstance(request_date, dt.datetime):
                # A valid date has been found, check whether we can now delete
                if request_date + dt.timedelta(days=days, hours=hours) <= dt.datetime.utcnow():
                    to_del.append((i, j))
        return self.clear_lines(self._done, to_del)


class Request(c.GenReq):
    "This object class will implement the main functionalities for a certain request"
    bot = c.NlBot()

    def __init__(self, target, types=(int,)):
        super().__init__(target, types)

    def process(self, inp):
        "This function will process the input fed to the constructor"
        if 'diff=' in inp and 'diff=prev' not in inp and 'diff=next' not in inp:  # Beware for a very special case
            return int(inp.split('&')[0].lower().replace('diff=', '').strip())
        # Make sure that we don't accidently query the &next revision (requires additional query)
        k = inp.lower()
        if k.count('/') > 1:  # Correct for a very specific case
            k = k.split('/')[-1].strip()
        # for i in ('oldid', 'permalink', 'diff', '=', '&', 'next', 'prev', 'special', 'speciaal', '/', ':', '{', '|'):
        #    k = k.replace(i, '') #Remove all these shitty stuff - old code
        # Testing :)
        k = re.findall(r'\d{7,}', inp.lower())[0]
        look_next = all((i not in inp.lower() for i in ['diff=next',
                                                        'direction=next']))  # Make an additional variable to check whether we should look at the next revision
        return int(k) if look_next else self.get_next_revision(int(k))

    def check_done(self):
        if self.done is False:
            "This function will check whether the request has been processed"
            dic = {'action': 'query',
                   'prop': 'revisions',
                   'revids': self.target,
                   'rvprop': 'content|timestamp|ids'}
            out = Request.bot.get(dic)
            t = next(iter(next(iter(out.get('query').values())).values()))
            self._page = t['title']
            p = t['revisions'][0]
            if 'texthidden' in p:
                self.done = True

    def check_person(self):
        'This function will check who did the request'
        dic = {'action': 'query',
               'list': 'logevents',
               'leprop': 'user|details',
               'letype': 'delete',
               'leaction': 'delete/revision',
               'letitle': self._page}
        out = Request.bot.get(dic)['query']['logevents']
        for i in out:
            k = i['params']
            if self.target in k['ids']:  # the revision involved was queried here
                if 'content' in k['new']:  # Will check whether the content of the revision was removed
                    self._user = i['user']
                    return i['user']

    def get_next_revision(self, prev, conti=None, jos=None):
        "This function gets the revision following a given revision. This function also supports continuation"
        if jos is None:  # Only run this if not passed
            d1 = {'action': 'query',
                  'prop': 'revisions',
                  'revids': prev,
                  'rvprop': 'ids'}
            jos = next(iter(Request.bot.get(d1)['query']['pages'].keys()))
        d2 = {'action': 'query',
              'prop': 'revisions',
              'rvlimit': 500,
              'rvprop': 'ids',
              'pageids': jos}
        if conti is not None:
            print('Repeating the query to find an old version of page %s.' % jos)  # For the log file
            d2['rvcontinue'] = conti
        bas = Request.bot.get(d2)  # This code should be stored, otherwise we cannot use the continuation function
        jef = next(iter(bas['query']['pages'].values()))['revisions']
        for i in jef:
            # print(i, 'Jef', prev)
            if i['parentid'] == prev:
                return i['revid']  # Revision found, should be enough
        # No valid revision was found, continue searching in the next revisions
        c = bas.get('continue')
        if c is not None:
            return self.get_next_revision(prev, c['rvcontinue'], jos)


class UserRequest(Request):
    def __init__(self, user):
        super().__init__(user, (str,))
        self._contribs, self._user = [], 'een moderator'

    def process(self, u):
        return u.strip().replace(']', '')

    def check_done(self):
        limit = dt.datetime.now().replace(microsecond=0) - dt.timedelta(200)  # Only check past 48 hours
        qdic = {'ucuser': self.target,
                'action': 'query',
                'list': 'usercontribs',
                'ucprop': 'ids',
                'uclimit': 500,
                'ucend': limit.isoformat()}
        q = Request.bot.get(qdic)['query']['usercontribs']
        for i in q:
            if i['revid'] not in self._contribs:
                self._contribs.append(i['revid'])
        self.done = all(('texthidden' in i for i in q))
        return bool(self)

    def done_string(self):
        "This function won't explicitly check who hid the revisions"
        return "De bijdragen van deze gebruiker zijn verborgen. Met dank voor de melding."

    def check_person(self):
        return self._user  # Just return None, as this function doesn't really do something


class MultiRequest(c.GenMulti):
    "This class can be used to check for a series of requests that would otherwise be filed in parallel."

    def __init__(self, req):
        assert all((isinstance(i, Request) for i in req)), 'Please only provide requests!'
        self.targets = []  # Use a tuple here
        self.users = []
        self.done = False  # This indicates whether the request was done
        self._titles, self._user = {}, None
        self.deleted = False
        for i in set(req):
            if isinstance(i, UserRequest):
                self.users.append(i)
            else:
                self.targets.append(i)

    def check_done(self):
        "This function will check whether the request has been processed"
        targets, users = False, False
        if self.done is False and self.targets:
            dic = {'action': 'query',
                   'prop': 'revisions',
                   'revids': '|'.join((str(i) for i in self.targets)),
                   'rvprop': 'content|timestamp|ids'}
            try:
                revs = Request.bot.get(dic)['query']['pages']
            except KeyError:
                self.deleted = True
                return bool(self)
            targets = all(('texthidden' in revs[i]['revisions'][0] for i in revs))
            self._titles = {i['revisions'][0]['revid']: i['pageid'] for i in revs.values()}
        if self.users:  # Check the edits per user
            users = all((i.check_done() for i in self.users))
        self.done = (targets or (not self.targets)) and (users or (not self.users))
        return bool(self)

    def check_person(self):
        'This function will check who did the request'
        if self.is_deleted():
            return "DELETED"
        if not self._titles:
            self.check_done()
        if self.targets:  # We have revisions that got selected
            self._user = self.targets[0].check_person()  # Just take the first one here
        else:
            self._user = self.users[0].check_person()
        return self.done_string()


t = Revdel()
t()  # Indien hier True wordt doorgegeven, draait het script in log-only mode, en worden geen veranderingen aangebracht
