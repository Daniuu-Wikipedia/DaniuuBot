"""
Maintenance file to clean logs on Toolforge.

My scripts generate a lot of logs, so they need to be cleaned regularly.

This script will clear the logs associated to the following jobs on a weekly basis:
    * Patroller-all (.err, .out, Log.txt, IPBLOK_log.txt, REGBLOK_log.txt)
    * archiver

The code verifies whether any errors occured (like, whether the .err file is empty) & then deletes the output files.
"""

import os
import json

parent_dir = os.path.split(os.path.dirname(os.path.abspath(__file__)))[:-1]  # Start directory

# Read the configuration file
with open('Configuration.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)  # And now read the whole lot

# On Toolforge, all jobs are executed in the main directory
os.chdir(parent_dir[0])


# Aux method
def is_empty_file(file):
    for i in file:
        if i.strip():
            return False
    return True


# Now start doing the run
for i in jobs['jobs']:
    if os.path.isfile(i['errorlog']):
        with open(i['errorlog'], 'r', encoding='utf-8') as f:
            if not is_empty_file(f):
                continue
        for j in i['clear']:
            if os.path.isfile(j):
                os.remove(j)
