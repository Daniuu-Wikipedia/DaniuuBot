#!/bin/bash

#For immediate execution of the revdel script

python -V
python3 -V

toolforge-jobs run revdel2 --command "./botenv/bin/python3.11 ./DaniuuBot/Request_patroller/Revdel_patrol.py" --image tf-python3.11 --wait

