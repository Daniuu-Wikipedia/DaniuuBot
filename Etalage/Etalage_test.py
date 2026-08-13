# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 17:55:19 2026

@author: Daniuu
"""

import Core
import json
import os
import random
from datetime import datetime

bot = Core.NlBot()

GLOBAL_SETTING = {'n_last': 1,
                  'n_penul': 1}

TARGET_CAT = 'Categorie:Wikipedia:Etalage-artikelen'

TARGET_PAGE = 'User:Daniuu/Etalage'


def get_etalage_pages_from_wiki():
    actd = {'action': 'query',
            'list': 'categorymembers',
            'cmtitle': TARGET_CAT,
            'cmprop': 'title|timestamp',
            'cmnamespace': 0,
            'cmtype': 'page',
            'cmlimit': 'max',
            'cmsort': 'timestamp',
            'cmdir': 'descending'}
    response = bot.get(actd)['query']['categorymembers']
    return len(response), sorted(response, key=lambda i: i['timestamp'], reverse=True)


def locate_configuration_file():
    # Locate the files
    location = 'Etalage_pages.json'
    if not os.path.isfile(location):
        # Configuration to be run from DaniuuBot account
        location = os.path.join(os.getcwd(),
                                'DaniuuBot',
                                'Etalage',
                                location)
    return location


def write_json_files(payload=None, preceding_permutation=None):
    """
    Writes the standardized JSON format file

    Parameters
    ----------
    payload: output of get_etalage_pages_from_wiki.
        Optional (not parsing will trigger an API call)
    last_new : TYPE, optional
        The number of last additions to the etalage to be considered separately.
        The default is 5.
    penultimate : TYPE, optional
        The number of almost last additions that gets separate treatment. 
        The default is 5.

    Returns
    -------
    None.
    Just writes the config file (with entirely new permutations)

    """
    location = locate_configuration_file()
    last_new, penultimate = GLOBAL_SETTING['n_last'], GLOBAL_SETTING['n_penul']
    
    if payload is None:
        payload = get_etalage_pages_from_wiki()
    
    # Writing new file = can't be done without a list of the category
    new_data = {'pages': [i['title'] for i in payload[1]]}
    
    # Arrange for the random shuffling of the party
    # We will always keep five new articles at the Etalage displayed
    # And five articles just before that
    # Exact numbers can be modified through last_new & penultimate arguments
    recent_order = list(range(last_new))
    random.shuffle(recent_order)
    penultimate_order = list(range(last_new, penultimate + last_new))
    random.shuffle(penultimate_order)
    other_order = list(range(penultimate + last_new, len(payload[1])))
    random.shuffle(other_order)  # Just leave these ids in, safer...
    if preceding_permutation is not None:
        # We need to incorporate part of the previous permutation into the new one
        # Method daily_update contains the tools needed to timely clean out any double entries... 
        # When adding new articles, we always add some articles
        # Indices will shift by a factor delta (implemented in daily_update)
        other_order = preceding_permutation + other_order  # Prepend remaining part of permutation
    
    # Write new orders 
    new_data['shuffles'] = {'recent': recent_order,
                            'penultimate': penultimate_order,
                            'others': other_order}
    
    with open(location, 'w', encoding='utf8') as outfile:
        json.dump(new_data, outfile, indent=4)
    
    return


def daily_update(fresh=1, total=8, new_stuff=0):
    # Read data from configuration file
    # Figure out where the config file is located
    location = locate_configuration_file()
    # Read file
    with open(location, 'r', encoding='utf8') as inputfile:
        data = json.load(inputfile)
    number, new = get_etalage_pages_from_wiki()
    if len(data['pages']) == number:
        del new  # No need to start updating configurations etc.
    else:
        # The json configuration requires a bit of updating (new page...)
        # What happened here?
        # New article(s) added to Etalage... - adjust the permutations
        delta = number - len(data['pages'])
        write_json_files((number, new), [i + delta for i in data['shuffles']['others']])
        return daily_update(new_stuff=delta)
    
    # What if some permutations are empty?
    # Regenerate the permuation
    if not data['shuffles']['recent']:
        data['shuffles']['recent'] = list(range(GLOBAL_SETTING['n_last']))
        random.shuffle(data['shuffles']['recent'])
    if not data['shuffles']['penultimate']:
        data['shuffles']['penultimate'] = [GLOBAL_SETTING['n_last'] + i for i in range(GLOBAL_SETTING['n_penul'])]
        random.shuffle(data['shuffles']['penultimate'])
    if not data['shuffles']['others']:
        vals = list(range(GLOBAL_SETTING['n_last'] + GLOBAL_SETTING['n_penul'], len(data['pages'])))
        random.shuffle(vals)
        data['shuffles']['others'] = vals 
        del vals
    
    # Another case: previous iteration => new articles => give them some extra visibility
    # Permutations are updated automatically further down the road
    if new_stuff > 0 and isinstance(new_stuff, int):
        data['shuffles']['recent'] = list(range(new_stuff)) * 2 + data['shuffles']['recent']
                
    # Select the pages that should be linked today
    # Order: total - 2*fresh random ones (decided when setting up the list)
    titles = [data['pages'][i] for i in data['shuffles']['others'][:(total - 2*fresh)]]
    titles += [data['pages'][i] for i in data['shuffles']['penultimate'][:fresh]]
    titles += [data['pages'][i] for i in data['shuffles']['recent'][:fresh]]
    titles.sort()  # Sort all titles, this can be adjusted upon request
    random.shuffle(titles)# Just for testing
    
    # Publish this list on the wiki
    # To be continued, pending some further discussions    
    format_text = 'style="border-bottom:1px solid #cccccc;padding:5px;"'
    wikitext = [r'{|style="width:100%;"']
    for i in titles[:-1]:
        wikitext += [f"|{format_text}| '''[[{i}]]'''",
                     '|-']
    final_style = '|style="padding:5px;"'
    wikitext += [f"{final_style}|'''[[{titles[-1]}]]'''",
                 r'|}<noinclude>',
                 '[[Categorie:Wikipedia:Sjablonen etalage|Hoofdpagina]]',
                 '[[Categorie:Wikipedia:Sjablonen hoofdpagina|Etalage]]',
                 '</noinclude>']
    
    # Post the updated text to the wiki
    edit_dic = {'action': 'edit',
                'title': TARGET_PAGE,
                'nocreate': True,
                'text': '\n'.join(wikitext),
                'summary': 'Testen v/e nieuw script',
                'bot': True}
    result = bot.post(edit_dic)
    
    assert 'error' not in result, f'ERROR while updating Etalage: {result}'
    
    print(f'SUCCESS {datetime.utcnow()}')
    
    
    # Update the permutation list & configuration file
    for i, j in data['shuffles'].items():
        data['shuffles'][i] = j[1:]  # Update permutations, avoid doing twice the same
    
    # Write updated configuration to the local file
    with open(locate_configuration_file(), 'w', encoding='utf8') as overfile:
        json.dump(data, overfile, indent=4)

    
    return


if __name__ == '__main__':
    # Test code, nothing to worry about
    # write_json_files()
    daily_update()