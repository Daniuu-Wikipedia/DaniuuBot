#!/bin/bash

#Delete the venv
bash ~/DaniuuBot/Toolforge_venv/Delete_venv.sh

#Recreate the venv
toolforge-jobs run venv-create --command "cd $PWD && ./Create_venv.sh" --image tf-python39 --wait
