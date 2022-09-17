# -*- coding: utf-8 -*-
"""
Created on Sun Sep 18 00:32:51 2022

@author: Daniuu

The script performs two actions
    1) If the script is executed on Toolforge, it restarts the relevant jobs (using an external script)
    2) The out of order messages are deleted from the relevant pages
"""

import datetime as dt
from Core import NlBot
from sys import platform
from os import getcwd

#Data for the first task
bash_loc = f'{getcwd()}/DaniuuBot/Toolforge_jobs.sh'

#Data for the second task
out_of_order_message = '{{Gebruiker:Daniuu/Buiten dienst}}' #Place brackets here for the template

pages = ('Wikipedia:Verzoekpagina voor moderatoren/Versies verbergen',
         'Wikipedia:Verzoekpagina voor moderatoren/IPBlok')

restart_summary = 'De bot is opnieuw opgestart'

#Perform the first task
if platform.startswith('linux'): #This task can only be performed on Linux-systems (like Toolforge)
    from os import system
    system(f'bash {bash_loc}')
else:
    raise ValueError('The jobs can only be restarted from Toolforge! Please run the script again there!')

#Define an auxilliary variable for the second task
bot = NlBot()

#Perform the second task
for i in pages:
    parse_date = dt.datetime.utcnow()
    payload = {'action':'parse',
               'page':i,
               'redirects':True,
               'prop':'wikitext'}
    content = bot.get(payload)['parse']['wikitext']['*']
    if out_of_order_message in content:
        content = content.replace(f'{out_of_order_message}\n', '')
        #Drop the corrected version
        edit_dic = {'action':'edit',
                    'title':i,
                    'notminor':True,
                    'bot':False, #To draw attention, this is not a routine edit
                    'nocreate':True,
                    'summary':restart_summary,
                    'text':'\n'.join(content),
                    'starttimestamp':parse_date.isoformat()}
        result = bot.post(edit_dic)
        if 'error' in result:
            if result['error']['code'] == 'editconflict':
                pages.append(i) #Make the page re-join the queue

#Acta est fabula, plaudite