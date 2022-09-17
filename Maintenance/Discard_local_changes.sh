#!/bin/bash

cd ~/DaniuuBot

#Shell script to discard all local changes in a repository
#To be used if the repo on Toolforge got inadvertendly changed

git reset --hard #Get rid of untracked changes
git clean -fd  #Get rid of untracked files in the repo
