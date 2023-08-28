"""
This file contains a set of parameters, directly read by the bot.

It is used to store some parameters that would otherwise be hardcodes at weird places in the code.
This file makes those parameters more easily accessible
"""

# Parameters influencing all bots (called from the Core)
# Strings that, if they appear on the page, stop the bot (use lowercase!)
abort_strings: tuple = ('{{nobots}}',
                        '{{nobots|deny=daniuubot',
                        '{{bots|deny=daniuubot}}')

# File in which the input for tests can be stored (to be located in the same directory as the code)
test_input: str = 'Bot_test_input.txt'
# File in which the output for tests can be stored (will be written into the same directory as the code)
# Be careful, writing an existing file here will overwrite it, possibly loosing all data stored therein
test_output: str = 'Bot_test_output.txt'

# Parameters influencing the bot patrolling nl:WP:VV
# Control the timespan between the handling and deletion of a revdel request (>= 1 days)
# Set to 2 days after https://w.wiki/7M7u (the request will remain visible for 1 day prior to being removed)
revdel_removal_days: int = 2  # Must be at least one (remove the day after the request got handled)
# Control the time in the morning (UTC) at which the removal will take place
# Note: this parameter does not account for differences in CET and CEST
revdel_removal_hours: int = 4  # Set to 4 (5 am in CET, 6 am in CEST - set this to a quiet time)


# Parameters influencing the bot patrolling WP:IPBLOK
# Not yet implemented
