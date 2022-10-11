# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 11:44:47 2021

@author: Student Daniel
"""
import datetime
import re
from Core import Bot

# this will be used to check whether the log file is an existing file
from os.path import exists
# To make it slightly easier to avoid issues with directories
from os.path import realpath, dirname
from os import chdir

chdir(realpath(dirname(__file__)))

class NlBot(Bot):
    def __init__(self):
        super().__init__('https://nl.wikipedia.org/w/api.php')


class Vote:
    'This class will implement all functions required to manage votes on the Dutch Wikipedia'
    API = 'https://nl.wikipedia.org/w/api.php'  # Use the same url for all instances

    def __init__(self, start, can, page):
        "This function will specifically implement the rules for nl-wiki (100 edits in the two weeks prior to start + 1 month activity)"
        self.start = start  # This value indicates when the vote will start
        # self.tw =  can #When the candicacy period starts
        # self.reg = datetime.datetime(start.year, start.month - 1, start.day, start.hour) #When a given user should be registered
        # self.ec = datetime.datetime(self.tw.year - 1, self.tw.month, self.tw.day, self.tw.hour) #Queries for one year prior to start of candid
        self.page = page  # The page that should be used for our tests
        self._bot = Bot(Vote.API)
        self.nc = 100  # Only users with 100+ edits are eligible to vote
        self._log = 'Logs.txt'
        self._checked = set()
        self.read_log()  # Read the log when creating the checker

    def check_user(self, user):
        "This function checks whether a user made at least the specified amount of contribitions (and whether an edit was made on time)"
        # Check whether the user made at least self.nc contributions in the interval
        p = {'action': 'query',
             'list': 'usercontribs',
             'uclimit': self.nc + 1,
             'ucstart': self.start - datetime.timedelta(weeks=2),
             'ucend': self.start - datetime.timedelta(weeks=2) - datetime.timedelta(weeks=52),
             'ucuser': user}
        l = len(self._bot.get(p)['query']['usercontribs'])

        # Check whether the editor made at least one edit prior to the self.reg treshold
        # p = {'action':'query',
        #     'list':'usercontribs',
        #     'uclimit':1,
        #     'ucuser':user,
        #     'ucdir':'newer',
        #     'ucprop':'title|timestamp'}
        #r = self._bot.get(p)['query']['usercontribs'][0]
        # d = datetime.datetime.strptime(r['timestamp'], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None) #Remove the timezone info

        # Return statement - will be used in further processing
        return user, l >= self.nc, l

    def read_log(self):
        "Reads the list of names that were already checked"
        if not exists(self._log):  # The log was not yet created
            with open(self._log, 'w') as newfile:
                newfile.write('Blokpop 69\n')
        with open(self._log, 'r') as datafile:
            for i in datafile:
                self._checked.add(i.split('\t')[0])

        return self._checked

    def write_log(self, lines):
        pass

    def get_page_content(self):
        "Gets the page content"
        pay = {'action': 'parse',
               'page': self.page,
               'prop': 'wikitext',
               'disabletoc': True}
        return self._bot.get(pay)['parse']['wikitext']['*']

    def update_log(self, new_lines):
        with open(self._log, 'a') as logfile:
            logfile.write('\n'.join(new_lines) + '\n')

    def __call__(self):
        "The main function (this one checks all relevant properties)"
        # Step 1: get the list of all users that have voted
        regex = r'#[^\}\/\|\]]+'
        raw = re.findall(regex, self.get_page_content())
        users = {i.split(':')[1].strip() for i in raw if ':' in i and 'Metaverse' not in i}
        newl, invalid = [], []  # New voters + their contribution
        work = users - self._checked  # No need to re-check users who voted before

        # Step 2: check whether the users are allowed to vote
        for i in work:
            check_result = self.check_user(i)
            newl.append('\t'.join((check_result[0], str(check_result[2]))))
            if check_result[1] is False:
                invalid.append((check_result[0], check_result[2]))
                print(f'User {check_result[0]} found on {datetime.datetime.utcnow()}')

        # Step 3: Update the log
        self.update_log(newl)

        # Step 4: Alert that there are users who are not eligible to vote
        if invalid:
            template = ['== Stemming ==',
                        'Beste Daniuu,\n',
                        f'Zou je volgende stemmen op [[{self.page}]] kunnen nakijken?']
            template += [f'* {i} heeft slechts {j} bijdrage(n) in de onderzochte 12 maanden.' for i, j in invalid]
            template += {'Vriendelijke groet, ~~~~'}
            pay = {'action':'edit',
                   'title':'Overleg gebruiker:Daniuu',
                   'nocreate':True,
                   'appendtext':'\n' + '\n'.join(template) + '\n',
                   'summary':'Melden van een mogelijke ongeldige stem'}
            print(self._bot.post(pay))


# Code for the arbcom elections of March 2021
start_vote = datetime.datetime(2022, 10, 11, 18)  # UTC TIME!!!
#cand = datetime.datetime(2021, 3, 11, 12)
page = "Wikipedia:Afzetting moderatoren"
#page = 'Gebruiker:Drummingman/kladblok3'
z = Vote(start_vote, None, page)
z()
