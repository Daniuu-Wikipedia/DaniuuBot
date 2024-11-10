"""
This module contains a list of block reasons that allow handling by the bot.

Two lists are implemented:
    1) `regblok_contains`: contains some key words. If these key words are present in the block reason, the bot will handle the request
    2) `regblok-matchesµ: the bot will only handle the request if this block reason is used exactly
"""

regblok_contains = ['vandaal',
                    'vandalisme',
                    'spam',
                    'spambot',
                    'ongewenste gebruikersnaam',
                    'sokpopmisbruik',
                    'sokpop']

regblok_matches = ['On request, to test a script']  # Just for development purposes
