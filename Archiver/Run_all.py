"""
Centralized script that reads the required runs from the configuration file
    & initiates the required archive runs.

This is the sole script to be called on Toolforge!
"""

import json  # Default library
import Archiver
import Date_utils


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
    temp = run_dict['archive_target'].replace('$YEAR', str(Date_utils.year))
    temp = temp.replace('$MONTH', str(Date_utils.month))
    run_dict['archive_target'] = temp.replace('$DAY', str(Date_utils.day))

    # Special case: REGBLOK parameter is present ==> make some substitutions there
    if '$REGBLOKNR' in run_dict['archive_target']:
        run_dict['archive_target'] = run_dict['archive_target'].replace('$REGBLOKNR',
                                                                        Date_utils.determine_regblok_archive_number(
                                                                            delay=run_dict['passed_dates']))
        print(Date_utils.determine_regblok_archive_number(delay=run_dict['passed_dates']))
    return run_dict  # Not needed, but good to return it anyway


def execute(run_dict):
    prepare_run(run_dict)
    page = Archiver.Page(run_dict)
    page.testing = True
    page()


# Actual execution
with open('Configuration.json', 'r') as config_file:
    config_data = json.load(config_file)['runs']
    for i in config_data:
        execute(i)
