"""
This file contains a set of parameters, directly read by the bot.

It is used to store some parameters that would otherwise be hardcodes at weird places in the code.
This file makes those parameters more easily accessible
"""

from datetime import timedelta  # To allow time intervals to be set

# Parameters influencing all bots (called from the Core)
# Strings that, if they appear on the page, stop the bot (use lowercase!)
# Pass an iterable
abort_strings = ('{{nobots}}',
                 '{{nobots|deny=daniuubot',
                 '{{bots|deny=daniuubot}}')

# File in which the input for tests can be stored (to be located in the same directory as the code)
# Please pass a string
test_input = 'Test_input.txt'
# File in which the output for tests can be stored (will be written into the same directory as the code)
# Be careful, writing an existing file here will overwrite it, possibly loosing all data stored therein
# Please pass a string
test_output = 'Bot_test_output.txt'
test_archive = 'Bot_test_archive.txt'

# List of pages to ignore (manual safety measure - not the most stylish, but works)
# Way of using: if a given title is in here, everything stops
abort_file = 'Bot_abort_file.txt'
