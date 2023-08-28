#!/bin/bash

cd ~/DaniuuBot

# Remove all the Python cache (directories __pycache__ and .pyc-files)
rm */*/*.pyc

git pull git@github.com:Daniuu-Wikipedia/DaniuuBot.git

cd ~/DaniuuBot/Maintenance

cp *.sh ~/Handy_scripts

# Safety measure: make sure that all .txt-files are properly chmodded (and invisble to other users)
cd ~/Handy_scripts
bash Perm.sh
