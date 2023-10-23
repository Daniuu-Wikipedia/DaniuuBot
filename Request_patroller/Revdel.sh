#!/bin/bash

#For immediate execution of the revdel script

toolforge-jobs run revdel2 --command "./botenv/bin/python ./DaniuuBot/Request_patroller/Revdel_patrol.py" --image tf-python3.11 --wait

