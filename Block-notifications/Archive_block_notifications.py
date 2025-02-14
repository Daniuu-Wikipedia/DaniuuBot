from Core import NlBot
import datetime as dt
import nldate_utils as nld

bot = NlBot()  # The bot to be used for all communications with betawiki

# Step 1: parse the content of WP:Blokkeringsmeldingen
title = 'Wikipedia:Blokkeringsmeldingen'
parse_dic = {'action': 'parse',
             'page': title,
             'prop': 'wikitext'}
# Retrieve the content of the page & remove excess whitespaces & separate lines
original_content = [i.strip() for i in bot.get(parse_dic)['parse']['wikitext']['*'].split('\n')]

# Step 2: define month & year to be archived
# Note: these variables can be changed by the developer whenever needed for testing
today = dt.date.today()
month = today.month - 1 if today.month > 1 else 12  # Month to archive
year = today.year if today.month > 1 else today.year - 1  # Year to archive

# Step 2: identify the sections in the content list
sections = [i for i, j in enumerate(original_content) if '==' in j]
sd = {i: original_content[i].count('=') // 2 for i in sections}  # Keep track of the level of each header

# Step 3: define auxiliary variables
# Two lists (1: bits of the old page to keep; 2: to copy to the new page)
# Copy is needed, otherwise, we mess up some of our stuff :)
keep_old, to_new = sections.copy(), sections.copy()
# And an auxiliary variable to handle any lines that don't have a date attached
no_date_line = None

# Step 4: Go through the content of the page and determine which lines are to be archived
for i, j in enumerate(original_content):
    date_found = nld.get_date_for_lines(j)
    if i < min(sections):
        keep_old.append(i)
    elif i in sections:  # No need to append, already happened above
        if isinstance(no_date_line, int):
            keep_old += list(range(no_date_line, i))  # We verify that no_date_line is an integer
            no_date_line = None  # Reset this value
    elif date_found is None:  # We're passing a line that does not have a date attached
        if no_date_line is None:
            no_date_line = i  # From here on, we have some problem
    else:  # We found a valid date :D
        # Next step: based on the date, determine whether the line(s) should be archived
        if date_found.year == year and date_found.month == month:
            to_new.append(i)
            if no_date_line is not None:
                to_new += list(range(no_date_line, i))
                no_date_line = None  # Reset
        else:
            keep_old.append(i)
            if no_date_line is not None:
                keep_old += list(range(no_date_line, i))
                no_date_line = None
# End of iterations (whole page got browsed)
# If there is still some unsigned content, assume that this does not need to be archived
if no_date_line is not None:
    keep_old += list(range(no_date_line, len(original_content)))

keep_old.sort()
to_new.sort()  # Sort these lists (we want everything to be listed in the right order)

# Reconstruct the content of the old page (like, the request page)
new_content_source = [original_content[i] for i in keep_old]

# Generate the actual content for the archive page
# Requires some additional post-processing
# Second, empty sections are thrown out (that's why we keep track of dictionary sd)
remove_sections = []
for i, j in zip(to_new[1:], to_new[:-1]):  # Last element will be handled seperately
    if j in sections and i in sections and sd[j] == sd[i]:
        remove_sections.append(j)

if to_new[-1] in sections:  # Deal with the last line as well (in all cases :) )
    remove_sections.append(to_new[-1])

for i in remove_sections:
    to_new.remove(i)

# Now, time to get the actual content :)
new_content_archive = [original_content[i] for i in to_new]
# Second: insert preamble into the archive
new_content_archive.insert(0, "__NOINDEX__\n{{mededeling|'''Dit is het archief van %s "
                              "%d van [[Wikipedia:Blokkeringsmeldingen]]'''.}}" % (nld.match[month].lower(),
                                                                                   year))

# Post the content of the archive now
target_archive = 'Wikipedia:Blokkeringsmeldingen/Archief/%d/%s' % (year,
                                                                   nld.match[month].lower())
edit_archive = {'action': 'edit',
                'title': target_archive,
                'text': '\n'.join(new_content_archive),
                'summary': 'Archivering van [[%s]] (%.02d-%d)' % (title, month, year),
                'notminor': True,
                'bot': True,
                'createonly': True}
out = bot.post(edit_archive)  # Log, also on Toolforge
print(out)
assert 'error' not in out, 'ERROR DETECTED, aborting the script!'

# Also protect the archive
protect_archive = {'action': 'protect',
                   'title': target_archive,
                   'protections': 'edit=sysop|move=sysop',
                   'reason': 'Archiefpagina'}
print(bot.post(protect_archive))

# Post the new content on the project page
edit_source = {'action': 'edit',
               'title': title,
               'text': '\n'.join(new_content_source),
               'summary': 'Verplaatsing naar [[%s|archief]] (%.02d-%d)' % (target_archive,
                                                                           month,
                                                                           year),
               'notminor': True,
               'bot': True}
print(bot.post(edit_source))
