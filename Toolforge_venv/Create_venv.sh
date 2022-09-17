#!/bin/bash

#Launch from the main directory
cd ~

# use bash strict mode
set -euo pipefail

# create the venv
python3 -m venv botenv

# activate it
source botenv/bin/activate

# upgrade pip inside the venv and add support for the wheel package format
pip install -U pip wheel

# install some concrete packages
pip install sys
pip install os
pip install requests
pip install pyyaml
pip install datetime
pip install re
pip install requests_oauthlib
pip install time
pip install math
