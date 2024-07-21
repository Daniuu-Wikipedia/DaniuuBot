"""
Centralized script that reads the required runs from the configuration file
    & initiates the required archive runs.

This is the sole script to be called on Toolforge!
"""

import json  # Default library
import Archiver
import Date_utils
import os


def prepare_run(run_dict):
    """
    Method reads the configuration file & substitutes all relevant parameters.
    Parameters are mainly taken from the date_utils module.

    Argument:
        * run_dict (dict): Dictionary for one run - will be processed.

    Returns:
        Dictionary
    """
    # Substitute date parameters in the archive name
    run_dict['archive_target'] = Date_utils.format_archive_for_date(Date_utils.current_time,
                                                                    run_dict['archive_target'])
    return run_dict  # Not needed, but good to return it anyway


def execute(run_dict):
    # prepare_run(run_dict)  # No longer used (due to migration of date formatting)
    page = Archiver.Page(run_dict)
    # page.testing = False  # Implemented for debugging purposes
    page()


# Make sure Toolforge also gets the right config file
if os.path.exists('Configuration.json'):
    file = 'Configuration.json'
else:
    file = os.path.join('DaniuuBot', 'Archiver', 'Configuration.json')

# Actual execution
with open(file, 'r') as config_file:
    config_data = json.load(config_file)['runs']
    for i in config_data:
        execute(i)
