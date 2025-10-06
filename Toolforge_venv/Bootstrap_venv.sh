#!/bin/bash

cd ~/Tools_venv
cp Create_venv.sh ~/Create_venv.sh

# Shell file to create the virtual environment using the desired Python interpreter
cd ~

# Chmod shell script, so it can be called directly by toolforge-jobs
chmod ug+x Create_venv.sh

# This command effectively starts the process of creating the environment
# Specify the --wait parameter! Other wise, the file will be chmodded back prematurely
toolforge-jobs run create-venv --command "cd $PWD && ./Create_venv.sh" --image python3.13 --wait

# Chmod it back, to stop it from being executed directly
chmod 740 Create_venv.sh
