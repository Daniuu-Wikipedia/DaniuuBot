#!/bin/bash

cd ~/DaniuuBot

#Safety measure
find ~/DaniuuBot -name "*.txt" -exec chmod 600 {} \;

#Prohibit the reading of shell files in the home directory by third parties
cd ~
chmod 700 *.sh
