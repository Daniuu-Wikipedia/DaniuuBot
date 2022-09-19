# -*- coding: utf-8 -*-
"""
Created on Sun Sep 18 03:08:34 2022

@author: Daniuu
"""

import datetime as dt

#This script is to be called from Toolforge when we need to change the used timezone
#Key variable: what zones are used when

#The code assumes that the switch occurs at the LAST SUNDAY of each month
#The code assumes that the switch occurs at 1 am UTC

#Define the timezones we switch to in which month
#Dictionary of the type {<month of the switch>:<new timezone>}
switches = {10:dt.timedelta(hours=-1),
            3:dt.timedelta(hours=-2)}

#Auxiliary function for the next steps
def find_last_day_per_month(month, year=None, day=6):
    """
    This function finds the last Sunday in a given month.
    If no year is passed, the current year is used
    """
    if year is None:
        year = dt.datetime.utcnow().year
    #Switches occur in months with 31 days
    last = dt.datetime(year, month, 31)
    if last.weekday() != day:
        last += dt.timedelta(days=-last.weekday() - (7 - day))
    return last + dt.timedelta(hours=1) #Add an extra hour to match the actual transition

#Determine when the switches occur in the present year
#mini is the first occuring change
#maxi is the latest occuring change
mini, maxi = min(switches.keys()), max(switches.keys())

#Find the exact days at which the transition occurs
swmini, swmaxi = find_last_day_per_month(mini), find_last_day_per_month(maxi)

#Now detemine what timezone we're in
now = dt.datetime.utcnow()

#VARIABLES CALLED BY OTHER MODULES
delta = switches[mini] if swmini <= now < swmaxi else switches[maxi]
offset = lambda x: switches[mini] if swmini <= x < swmaxi else switches[maxi]

print(delta)