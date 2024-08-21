"""
Copies Core.py file to the subfolders of the development directory that rely on these codes...

This file is solely intended for development purposes

@author: Daniuu-Wikipedia
"""

import os
import shutil

# Define the list of subdirectories to ignore
ignore_list = ['Core',
               'Maintenance',
               'Toolforge_venv']  # Replace with your actual subdirectory names

# Define the files to be moved
files_to_copy = ['Core.py',
                 'nldate_utils.py']

# Get the parent directory of the current working directory
parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

# List all subdirectories in the parent directory
subdirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]

# Filter out the subdirectories in the ignore list and those starting with '.'
subdirs = [d for d in subdirs if d not in ignore_list and not d.startswith('.')]

# Path to the Core.py file in the current directory
core_file_path = os.path.join(os.getcwd(), 'Core.py')

# Move Core.py to each remaining subdirectory
for subdir in subdirs:
    for file in files_to_copy:
        dest_path = os.path.join(parent_dir, subdir, file)
        shutil.copy2(core_file_path, dest_path)
    if '__pycache__' in os.listdir(os.path.join(parent_dir, subdir)):
        shutil.rmtree(os.path.join(parent_dir, subdir, '__pycache__'))

print("Core.py has been moved to all specified subdirectories.")
