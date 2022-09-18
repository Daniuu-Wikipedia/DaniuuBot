#!/bin/bash

cd ~/DaniuuBot

#Define colors for output (https://ansi.gabebanks.net/ and https://linuxhandbook.com/change-echo-output-color/)
GREEN='\033[32;1m' #Also bold
RED='\033[0;31;1m'
NOCOLOR='\033[0m'
YELLOW='\033[33m'
CYAN='\033[36m'
BLUE='\033[34m'
MAGENTA='\033[35m'

#Restarts the bot
echo -e "${YELLOW}Restarting${NOCOLOR} the bot. I will use an auxiliary script for this"

bash Reset_Toolforge_jobs.sh

#When complete, submit a job to Kubernetes to remove the out of order message
cd ~/DaniuuBot/Request_patroller

toolforge-jobs run restart-bot --command "./botenv/bin/python ./DaniuuBot/Request_patroller/Py_Restart_bot.py" --image tf-python39 
