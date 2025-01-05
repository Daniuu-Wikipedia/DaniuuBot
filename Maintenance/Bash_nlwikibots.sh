#!/bin/bash

cd ~/bots/old-daniuu/DaniuuBot

# Safety measure
# We do not want other people to be able to read our tokens!
find ~/bots/old-daniuu/DaniuuBot -name "*.txt" -exec chmod 600 {} \;

# Prohibit the reading of shell files in the home directory by third parties
cd ~/Handy_scripts
chmod 700 *.sh
