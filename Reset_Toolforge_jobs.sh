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


# Job to patrol WP:VV & WP:IPBLOK
toolforge-jobs run patroller-all --command "./botenv/bin/python ./DaniuuBot/Request_patroller/Run_all.py" --image python3.11 --schedule "*/10 * * * *"
echo -e "Job to patrol request pages ${GREEN}successfully${NOCOLOR} submitted to the ${CYAN}Kubernetes engine${NOCOLOR}."

# Archiver
toolforge-jobs run archiver --command "./botenv/bin/python3.11 ./DaniuuBot/Archiver/Run_all.py" --image python3.11 --schedule "13 2 * * *" --retry 3

echo -e "Job to run the Archiver submitted to the ${CYAN}Kubernetes engine${NOCOLOR}."

# 20241110 - Internal cleanup of logs
toolforge-jobs run logcleaner --command "./botenv/bin/python3.11 ./DaniuuBot/Maintenance/Remove_logs.py" --image python3.11 --schedule "@weekly" --emails onfailure
echo -e "Job to run the log cleaner submitted to the ${CYAN}Kubernetes engine${NOCOLOR}."

# Just write a message that we're done submitting jobs to the grid
echo -e "I have ${GREEN}SUCCESSFULLY${NOCOLOR} submitted the jobs I had to submit!"
