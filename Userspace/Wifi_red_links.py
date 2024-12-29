"""

A script requested by Themanwithnowifi

Actions of the script:

1) Get a list of red links from https://nl.wikipedia.org/wiki/Gebruiker:Themanwithnowifi/Rode_Links
2) Scan which links in that list have already been created
3) Remove the links that were created (blue ones, colloquially)
4) Report the number of articles that got created

"""

# Import required modules
from Core import NlBot
import re
import time  # To log the time on Toolforge
import datetime as dt  # For logging on Toolforge

print(f'\nStarting run at {dt.datetime.now()}Z')  # To log performance on Toolforge


# Auxiliary function
def clean_matches(s, boot: tuple = ('|', '[', ']')):
    if isinstance(s, str):
        for char in boot:
            s = s.replace(char, '')
        s = s.replace('_', ' ')
    elif isinstance(s, list):
        s = tuple((clean_matches(i) for i in s))
    return s


# First job: get a list of links
bot = NlBot()

target = 'Gebruiker:Themanwithnowifi/Rode Links'

start = float(time.time())  # To check the performance of the various API queries

dic1 = {'action': 'parse',
        'page': target,
        'prop': 'links'}

linklist = bot.get(dic1)['parse']['links']

existing_links = {i['*'] for i in linklist if 'exists' in i.keys()}
del linklist  # Just saving some memory

t1 = float(time.time())
print(f'Done loading links on the page, time needed {t1 - start} s')

# Required to update the page at the end of the journey
dic2 = {'action': 'parse',
        'page': target,
        'prop': 'wikitext|revid'}

inter2 = bot.get(dic2)['parse']
baserev = inter2['revid']
page_text = inter2['wikitext']['*'].split('\n')
del inter2  # Save some memory

t2 = float(time.time())
print(f'Getting the full wikitext done in {t2 - t1} s')

# Time to check whether the links exist or whether they don't
to_del = []  # List of lines to delete

resolved = 0

regex = r'\[{2}.+?[\|\]]'

for i, j in enumerate(page_text):
    if not j:
        to_del.append(i)
    else:
        link = clean_matches(re.findall(regex, j))
        if link:  # Only continue if we found a link in the line
            if link[0] in existing_links:
                to_del.append(i)
                resolved += int(j.split('-')[-1].strip())

to_del.sort(reverse=True)

t3 = float(time.time())
print(f'Wikilinks screened in {t3 - t2} s')

for i in to_del:
    del page_text[i]

t4 = float(time.time())
print(f'Wikitext cleanup done in {t4 - t3} s')

# Post the new content of the page
editdic = {'action': 'edit',
           'title': target,
           'baserevid': baserev,  # TO BE COMPLETED!!!
           'notminor': True,
           'bot': False,
           'text': '\n'.join(page_text),
           'nocreate': True,
           'summary': "%d pagina's uit de lijst zijn aangemaakt; %d rode links opgelost" % (len(to_del), resolved)}

output = bot.post(editdic)
print(output)
assert 'error' not in output, "Error found in output"
et = float(time.time())
print(f'Editing page took {et - t4} s')
print(f'RUN DONE - total runtime {et - start} seconds')

print(f'Run terminated at {dt.datetime.now()}Z\n-----')
