#!/bin/bash

# Move to the correct directory (TOOLFORGE !!!)
cd ~/bots/old-daniuu/DaniuuBot

# Remove all the Python cache (directories __pycache__ and .pyc-files)
rm */*/*.pyc

git pull git@github.com:Daniuu-Wikipedia/DaniuuBot.git


# Move scripts in the "Maintanance section" to a home directory - easier access
cd ~/bots/old-daniuu/DaniuuBot/Maintenance

cp *.sh ~/bots/old-daniuu/Handy_scripts

# Safety measure: make sure that all .txt-files are properly chmodded (and invisble to other users)
cd ~/bots/old-daniuu/Handy_scripts
bash Bash_nlwikibots.sh

# Additional task: copy the updated Core.py file
# Not always used!
cd ~/bots/old-daniuu/DaniuuBot/Core
python3 Copy_to_subfolders.py
