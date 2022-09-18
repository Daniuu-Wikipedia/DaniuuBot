#!/bin/bash

cd ~/DaniuuBot/Request_patroller

#Define colors for output (https://ansi.gabebanks.net/ and https://linuxhandbook.com/change-echo-output-color/)
GREEN='\033[32;1m' #Also bold
RED='\033[0;31;1m'
NOCOLOR='\033[0m'
YELLOW='\033[33m'
CYAN='\033[36m'
BLUE='\033[34m'
MAGENTA='\033[35m'

#Submits the job to stop
echo -e "${RED}Stopping${NOCOLOR} the bot. I will submit the stopping Python script."

toolforge-jobs run restart-bot --command "./botenv/bin/python ./DaniuuBot/Request_patroller/Py_Start_maintenance" --image tf-python39 

echo -e "$Job {GREEN}sumbitted."
