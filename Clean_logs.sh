#!/bin/bash

#Great, now switch to the home directory
cd ~ 

#Get the current date (in dd/mm/yy)
now=$(date +"%d_%m_%Y")

#Generate the new filename
nomen=$"/logs/Revdel_$now.log"

#Move the revdel.out script to the logs folder
mv Revdel.out $nomen

#DONE
