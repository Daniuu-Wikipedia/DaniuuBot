"""
This file contains a set of parameters, directly read by the bot.

It is used to store some parameters that would otherwise be hardcodes at weird places in the code.
This file makes those parameters more easily accessible
"""

from datetime import timedelta  # To allow time intervals to be set

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
# Control the timespan between the handling and deletion of a request to block an IP (>= 1 days)
# Set to 1 day, per preceding common practice
ipblok_removal_days: int = 1  # Must be at least one (remove the day after the request got handled)
# Control the time in the morning (UTC) at which the removal will take place
# Note: this parameter does not account for differences in CET and CEST
ipblok_removal_hours: int = 4  # Set to 4 (5 am in CET, 6 am in CEST - set this to a quiet time)
# Control the timespan between the block and the request being processed
# Allows the blocking sysop to make a statement on their block (if they wish to do so)
# Per previously-used settings, 10 minutes is taken
ipblok_processing_delay_minutes: int = 10
# Define which old blocks the bot ignores
# Blocks older than the indicated timedelta will not be handled by the bot
# As per previous practice, this value is set to 1 hour
ipblok_block_expiry: timedelta = timedelta(hours=1)
