# -*- coding: utf-8 -*-
"""
Created on Fri Aug 13 23:39:59 2021

@author: Daniuu

This script synchronizes my userpages on nlwiki and vlswiki
"""

from Core_UP import NlBot, VlsBot

def get_original_text():
    bot = NlBot() #Prepare the correct bot
    payload = {'action':'parse',
               'page':'Gebruiker:Daniuu',
               'prop':'wikitext'}
    return bot.get(payload)['parse']['wikitext']['*'].split('\n')

def remove_templates(text):
    "This method removes all sorts of unwanted templates from the page"
    out = []
    for i in text:
        if '{{' not in i or r'#babel' in i:
            out.append(i)
    return out

def remove_divisions(text):
    "This method removes a second bunch of unwanted content"
    t1 = [i for i in text if '<div' not in i and '</div>' not in i and 'Wikipedia:' not in i] #Remove all divisions
    t2 = [i.replace('Bestand:', 'File:') for i in t1] #Fix a very common bug
    return t2

def post_new_text(new):
    bot = VlsBot()
    payload = {'action':'edit',
               'title':'Gebruker:Daniuu',
               'text':new,
               'bot':True}
    return bot.post(payload)

def get_old_text():
    bot = VlsBot()
    payload = {'action':'parse',
               'page':'Gebruker:Daniuu',
               'prop':'wikitext'}
    return bot.get(payload)['parse']['wikitext']['*']
text = get_original_text()
s1 = remove_templates(text)
s2 = remove_divisions(s1)
new = '\n'.join(s2)

old_text = get_old_text()

if old_text != new:
    print(post_new_text(new))
