# -*- coding: utf-8 -*-
"""
Created on Sun Sep 18 00:32:51 2022

@author: Daniuu

The script performs one main action
    1) The out of order messages are deleted from the relevant pages
"""

import datetime as dt
from Core import NlBot

# Data for the task
out_of_order_message = '{{Gebruiker:Daniuu/Buiten dienst}}'  # Place brackets here for the template

pages = ('Wikipedia:Verzoekpagina voor moderatoren/Versies verbergen',
         'Wikipedia:Verzoekpagina voor moderatoren/IPBlok')

restart_summary = 'De bot is opnieuw opgestart'

# Define an auxilliary variable for the task
bot = NlBot()

# Perform the task
for i in pages:
    parse_date = dt.datetime.utcnow()
    payload = {'action': 'parse',
               'page': i,
               'redirects': True,
               'prop': 'wikitext'}
    content = bot.get(payload)['parse']['wikitext']['*']
    if out_of_order_message in content:
        content = content.replace(f'{out_of_order_message}\n', '')
        # Drop the corrected version
        edit_dic = {'action': 'edit',
                    'title': i,
                    'notminor': True,
                    'bot': False,  # To draw attention, this is not a routine edit
                    'nocreate': True,
                    'summary': restart_summary,
                    'text': content,
                    'starttimestamp': parse_date.isoformat()}
        result = bot.post(edit_dic)
        if 'error' in result:
            if result['error']['code'] == 'editconflict':
                pages.append(i)  # Make the page re-join the queue

# Acta est fabula, plaudite
