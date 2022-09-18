# -*- coding: utf-8 -*-
"""
Created on Sun Sep 18 00:01:50 2022

@author: Daniuu

A file to automate the process that starts maintenance.

The script performs two actions
    1) An 'out of order'-message is placed on dedicated pages of the Dutch Wikipedia
"""

from Core import NlBot
import datetime as dt
from sys import platform

#Setting of parameters for the first task
out_of_order_message = '{{Gebruiker:Daniuu/Buiten dienst}}' #Place brackets here for the template

pages = ('Wikipedia:Verzoekpagina voor moderatoren/Versies verbergen',
         'Wikipedia:Verzoekpagina voor moderatoren/IPBlok')

pos_before = '= Verzoeken =' #The text before which we need to place the "out of order message"

stop_summary = 'De bot wordt buiten dienst gesteld voor onderhoud'

#Parameters for the second task
job_names = ('ipblok', 'revdel') #A list of jobs that must be terminated during the maintenance

#Defining auxiliary variables for the first task
bot = NlBot() #The bot that we will use

#Run the first task
for i in pages: #Browse through the relevant pages
    parse_date = dt.datetime.utcnow()
    payload = {'action':'parse',
               'page':i,
               'redirects':True,
               'prop':'wikitext'}
    content = bot.get(payload)['parse']['wikitext']['*']
    if not out_of_order_message in content: #We should only continue if the message has not yet been placed
        split = content.strip().split('\n') #Split the string into its relevant lines
        insert_pos = split.index(pos_before)
        split.insert(insert_pos, out_of_order_message) #Insert the message that the bot is out of order 
        edit_dic = {'action':'edit',
                    'title':i,
                    'notminor':True,
                    'bot':False, #To draw attention, this is not a routine edit
                    'nocreate':True,
                    'summary':stop_summary,
                    'text':'\n'.join(split),
                    'starttimestamp':parse_date.isoformat()}
        result = bot.post(edit_dic)
        if 'error' in result:
            if result['error']['code'] == 'editconflict':
                pages.append(i) #Make the page re-join the queue
    else:
        print(f'Maintenance message was already on {i}')