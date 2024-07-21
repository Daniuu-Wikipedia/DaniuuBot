#!/bin/bash

#For immediate execution of the patrol script

toolforge-jobs run archive --command "./botenv/bin/python3.11 ./DaniuuBot/Archiver/Run_all.py" --image python3.11 --wait
