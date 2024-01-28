"""

A script requested by Themanwithnowifi

Actions of the script:

1) Get a list of red links from https://nl.wikipedia.org/wiki/Gebruiker:Themanwithnowifi/Rode_Links
2) Scan which links in that list have already been created
3) Remove the links that were created (blue ones, colloquially)
4) Report the number of articles that got created

"""

# Import required modules
from Core_UP import NlBot
import re


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

dic1 = {'action': 'parse',
        'page': target,
        'prop': 'links'}

linklist = bot.get(dic1)['parse']['links']

existing_links = {i['*'] for i in linklist if 'exists' in i.keys()}

# Required to update the page at the end of the journey
dic2 = {'action': 'parse',
        'page': target,
        'prop': 'wikitext'}

page_text = bot.get(dic2)['parse']['wikitext']['*'].split('\n')

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

for i in to_del:
    del page_text[i]

# Post the new content of the page
editdic = {'action': 'edit',
           'title': target,
           'notminor': True,
           'bot': False,
           'text': '\n'.join(page_text),
           'nocreate': True,
           'summary': "%d pagina's uit de lijst zijn aangemaakt; %d rode links opgelost" % (len(to_del), resolved)}

print(bot.post(editdic))
