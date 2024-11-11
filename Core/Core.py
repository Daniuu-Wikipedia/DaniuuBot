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

# Before taking any actions, change the UA to something nicer
set_user_agent('Daniuu-Bot')


# Functionality to allow logging
def clear_log_file(file):
    with open(file, 'w', encoding='utf8') as blankfile:
        blankfile.write('%s\n' % (dt.datetime.utcnow()))


def log(file, text):
    with open(file, 'a', encoding='utf8') as logfile:
        logfile.write(text.rstrip() + '\n')


# Convenient utility: get prefix for discussion entry
def get_prefix(pre):
    if "*" in pre:
        return '*' * (pre.count('*') + 1)
    elif ":" in pre:
        return ':' * (pre.count(':') + 1)
    else:
        return ':'


class Bot:
    'This class is designed to facilitate all interactions with Wikipedia (and to get the processing functions out of other calsses)'
    max_edit = 5  # The maximum number of edits that a single bot can do per minute

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

    def post(self, params, force_s = False):
        assert 'action' in params, 'Please provide an action'
        if force_s is True:
            self.verify_OAuth('GS.txt')
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
        if force_s is True:
            self.verify_OAuth()
        return k


class NlBot(Bot):
    max_edit = 12  # We have a bot flag on nlwiki ==> allow 12 edits per minute for this one
    timestamps_all = []  # All timestamps of all bots

    def __init__(self):
        super().__init__('https://nl.wikipedia.org/w/api.php')
        self._max = NlBot.max_edit

    def post(self, params):  # Centralizes all runs & prevents DaniuuBot from making > 12 edits/min on nlwiki
        self.ti = NlBot.timestamps_all
        k = super().post(params)
        NlBot.timestamps_all.append(self.ti[-1])  # Be careful: other instances might also pop up
        return k


class BetaBot(Bot):
    """This is a bot that will allow for editing from the BetaWiki of the Dutch Wikipedia"""

    def __init__(self):
        super().__init__("https://nl.wikipedia.beta.wmflabs.org/w/api.php")

    def verify_OAuth(self):
        super().verify_OAuth('Beta.txt')


class TestBot(Bot):
    def __init__(self):
        super().__init__('https://test.wikipedia.org/w/api.php')


# Exception to deal with forcibly aboorted bot runs
class Aborted(Exception):
    def __str__(self):
        return 'BOT was stopped due to a stop trigger, like {{nobots}} being used!'


class API_Error(Exception):
    def __init__(self, name):
        super().__init__()
        self._name = name

    def __str__(self):
        return 'API Error ==> ABORTING BOT; error occured while handling page "%s"' % self._name
