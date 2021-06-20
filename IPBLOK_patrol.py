# -*- coding: utf-8 -*-
"""
Created on Sun Jun 20 12:21:36 2021

@author: Daniuu

This script is designed to automatically patrol the Dutch Wikipedia IPBLOK-request page
Please note: this script is still in an experimental phase, 
"""

import Core as c
import datetime as dt
import re


class IPBLOK(c.Page):
    "This class contains the main content for the page related operations"
    def __init__(self):
        super().__init__('Wikipedia:Verzoekpagina voor moderatoren/IPBlok')
    
    def separate(self):
        return super().separate('Nieuwe verzoeken', 'Afgehandelde verzoeken')
    
    def check_request_on_line(self, line):
        "This method checks whether a request was placed on the line"
        ip4 = r'' #Regex pattern used to detect ip4-adresses (and ranges)
        ip6 = r'' #Regex pattern used to detect ip4-adresses (and ranges)
        templates = ('lg', 'lgipcw', 'lgcw', 'linkgebruiker', 'Link IP-gebruiker cross-wiki', 'lgx')
        regex_template = r'\{\{(%s)\|'%('|'.join(templates)) #A pattern that makes handling the templates easier
        return regex_template
    

class Test(IPBLOK):
    "The function that should be put to testwiki"
    def __init__(self):
        super().__init__()
        self.name = 'Verzoekpagina'
        self.bot = c.TestBot()
    
    def format_date(self, date):
        "Overrides this with the conventions for testwiki"
        assert isinstance(date, str), "Please pass a string as the argument of format_nldate!"
        for k, l in c.Page.testdate.items():
                date = date.replace(k, l)
        return dt.datetime.strptime(date, '%d %m %Y') #this is the object that can actually do the job for us

k = Test()
k.get_page_content()
k.separate()
print(k.check_request_on_line(None))