#!/bin/bash

cd ~/DaniuuBot

# Remove all the Python cache (directories __pycache__ and .pyc-files)
rm */*/*.pyc

git pull git@github.com:Daniuu-Wikipedia/DaniuuBot.git


# Move scripts in the "Maintanance section" to a home directory - easier access
cd ~/DaniuuBot/Maintenance

cp *.sh ~/Handy_scripts

# Also move the scripts relating to the Virtual environment
cd ~/DaniuuBot/Toolforge_venv
cp *.sh ~/Tools_venv

# Safety measure: make sure that all .txt-files are properly chmodded (and invisble to other users)
cd ~/Handy_scripts
bash Perm.sh

# Additional task: copy the updated Core.py file
# Not always used!
cd ~/DaniuuBot/Core
python3 Copy_to_subfolders.py
