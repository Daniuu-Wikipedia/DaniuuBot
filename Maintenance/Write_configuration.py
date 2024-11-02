"""
File to write the configuration file used by the Remove_logs.py script

The configuration file is a .json file and uses the following format:
    * Name of the job (as key)
        * Name of the file containing the errors
        * Name of the file(s) to be deleted if there are no errors
"""

import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Code for the patroller job
patrol = {'clear': ['patroller-all.err',
                    'patroller-all.out',
                    'Log.txt',
                    'IPBLOK_log.txt',
                    'REGBLOK_log.txt'],
          'errorlog': 'patroller-all.err'}

# Code for the archiver job
archiver = {'clear': ['archiver.err',
                      'archiver.out'],
            'errorlog': 'archiver.err'}

# And now time to actually write the json
content = {'jobs': [patrol,
                    archiver]}

with open('Configuration.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(content, indent=4))
