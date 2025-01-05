"""
Developed to synchronise the config file of the bot to it's nlwiki equivalent

WARNING: the configuration file is read directly from nlwiki

DO NOT UNPROTECT THE NLWIKI PAGE!!!
"""

import json
import os
import datetime as dt
from Core import NlBot

# Can simply be executed as a script (the task is straight-forward)
# Step 1: get text from the wiki page
parse_dic = {'action': 'parse',
             'page': 'Gebruiker:Daniuu/Archiver configuration.json',
             'prop': 'wikitext'}

jos = NlBot()
parsed_text = jos.get(parse_dic)['parse']['wikitext']['*']

# Step 2: parse the obtained string as
json_parsed = json.loads(parsed_text)

# Step 3: Write the new Json
config_json = 'Configuration.json'
if not os.path.exists(config_json):
    os.chdir(os.path.join('bots',
                          'old-daniuu',
                          'DaniuuBot',
                          'Archiver'))

with open(config_json, 'w', encoding='utf8') as outfile:
    json.dump(json_parsed,
              outfile,
              indent=4)

# Step 4: for internal logging: store the date
with open('Config_sync.txt', 'w', encoding='utf8') as outfile:
    outfile.write('Last sync of JSON: ' + str(dt.datetime.utcnow()) + ' UTC')
