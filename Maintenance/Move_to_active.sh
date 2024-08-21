#!/bin/bash

# Define the target directory
TDIR="~/Active"

cd ~/DaniuuBot

# Moves all code to the directory that contains the active code for the bot
# First: Core of the device
cp Core/Core.py $TDIR

# Second: Code used for the archiver
cp Archiver/*.py $TDIR
cp Archiver/*.sh $TDIR

# Third: code used for the request patroller
cp Request_patroller/*.py $TDIR
cp Request_patroller/*.sh $TDIR
