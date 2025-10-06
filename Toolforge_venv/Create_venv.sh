#!/bin/bash

# Make sure the correct Python interpreter is selected before launching!
#Launch from the main directory
cd ~

# use bash strict mode
set -euo pipefail

# create the venv
python3 -m venv venv-tf-python311

# activate it
source venv-tf-python311/bin/activate

# upgrade pip inside the venv and add support for the wheel package format
pip install -U pip wheel

# install some concrete packages
pip install requests
pip install pyyaml
pip install mwoauth
pip install Flask
pip install requests_oauthlib
pip install toolforge
pip install pytz  # To deal with timezones
pip install PyMySQL  # Sync with nlwikibots requirements
pip install pywikibot  # Not used by DaniuuBot, but required for other nlwikibots repositories
pip install mwparserfromhell  # Also a pretty firm requirement :)
pip install mwcomposerfromhell  # One more package - to transform into
