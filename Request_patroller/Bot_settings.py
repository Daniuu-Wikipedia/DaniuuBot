"""
This file contains a set of parameters, directly read by the bot.

It is used to store some parameters that would otherwise be hardcodes at weird places in the code.
This file makes those parameters more easily accessible
"""

# Parameters influencing the bot patrolling nl:WP:VV
# Control the timespan between the handling and deletion of a revdel request (>= 1 days)
# Set to 2 days after https://w.wiki/7M7u (the request will remain visible for 1 day prior to being removed)
revdel_removal_days: int = 2  # Must be at least one (remove the day after the request got handled)
# Control the time in the morning (UTC) at which the removal will take place
# Note: this parameter does not account for differences in CET and CEST
revdel_removal_hours: int = 4  # Set to 4 (5 am in CET, 6 am in CEST - set this to a quiet time)
