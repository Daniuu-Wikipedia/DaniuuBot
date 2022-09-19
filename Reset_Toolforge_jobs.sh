#!/bin/bash

#Define colors for output (https://ansi.gabebanks.net/ and https://linuxhandbook.com/change-echo-output-color/)
GREEN='\033[32;1m' #Also bold
RED='\033[0;31;1m'
NOCOLOR='\033[0m'
YELLOW='\033[33m'
CYAN='\033[36m'
BLUE='\033[34m'
MAGENTA='\033[35m'

#Script to reset the jobs running on Kubernetes
echo -e "I will ${RED}delete all existing jobs${NOCOLOR} that are currently running."

toolforge-jobs flush

echo -e "${YELLOW}I have deleted all existing jobs."
echo -e "${NOCOLOR}I will now resubmit the required jobs"

#Job to patrol https://nl.wikipedia.org/wiki/Wikipedia:Verzoekpagina_voor_moderatoren/Versies_verbergen
toolforge-jobs run revdel --command "./botenv/bin/python ./DaniuuBot/Request_patroller/Revdel_patrol.py" --image tf-python39 --schedule "*/15 * * * *"

echo -e "Job to patrol WP:VV ${GREEN}successfully${NOCOLOR} submitted to the ${CYAN}Kubernetes engine${NOCOLOR}."

#Job to patrol https://nl.wikipedia.org/wiki/Wikipedia:Verzoekpagina_voor_moderatoren/IPBlok
toolforge-jobs run ipblok --command "./botenv/bin/python ./DaniuuBot/Request_patroller/IPBLOK_patrol.py" --image tf-python39 --schedule "02,12,22,32,42,52 * * * *"

echo -e "Job to patrol WP:IPBLOK ${GREEN}successfully${NOCOLOR} submitted to the ${CYAN}Kubernetes engine${NOCOLOR}."

#Job to synchonize my nlwiki and vlswiki user pages
toolforge-jobs run up-sync --command "./botenv/bin/python ./DaniuuBot/Userpage_synchroniser/Copy_userpage.py" --image tf-python39 --schedule "20 4 * * *"

echo -e "Job to sync your vlswiki and nlwiki user pages ${GREEN}successfully${NOCOLOR} submitted to the ${CYAN}Kubernetes engine${NOCOLOR}."
