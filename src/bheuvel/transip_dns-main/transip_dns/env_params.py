# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Functions for processing environment variables into command line parameters.

process_environment_variables: actual integration of environment
variables (injected) into the command line parameters.

deduce_environment_variable: a fixed method of relating commandline
parameters (names) with an environment variable.

use_env_variables: check if the environment variable is used,
and not used on the command line.



This module is not how argparse should be extended and this can very
well be considered a "dirty hack", or backdoor as it manipulates the
commandline parameters (sys.argv) before argparse does it's parsing!

Alternatives:
- https://pypi.org/project/ConfigArgParse/
    Downsides:
    - Does not support 'nargs="?"', in this case used
      with "--query_ipv4" as switch and
      "--query_ipv4 https://ipv4.icanhazip.com" parameter with option.
    - Repository has no activity (from maintainer) for 10 months.
- A commonly mentioned short piece of code
    (https://stackoverflow.com/a/10551190)
  (Same with any other options (ab)use extending argparse.Action)
    Downsides:
    - Does not support nargs="?" (optional value for a parameter)
    - Does not support mutually exclusive groups
    - Does not support action='store_true'
"""
import os
import sys
from argparse import ArgumentParser


def use_env_variables(env_var: str, option_strings: list) -> bool:
    """Determine if the environment setting needs to be used.

    Not the case when the commandline switch is already present

    :param env_var: environment variable to be checked
    :type env_var: str
    :param option_strings: option strings of the respective variable
    :type option_strings: list
    :return: whether this specific parameter (environment variable)
             needs to be inserted
    :rtype: bool
    """
    if env_var in os.environ:
        # Environment variable exists,
        # now check if already provided as command line parameter
        count_option_strings = len(option_strings)
        unused_option_strings = len(set(option_strings) - set(sys.argv))

        return unused_option_strings == count_option_strings
    else:
        return False


def deduce_environment_variable(option_strings: list) -> str:
    """Deduce the environment name from the long option name of the parameter.

    Every parameter has a long named option and is last in the list. The last
    in the list will be assumed to resemble the environment variable.

    E.g. "-q", "--query_ip", "--query_ipv4" --> TID_QUERY_IPV4

    :param option_strings: list of options for this specific parameter
    :type option_strings: list
    :return: the generated environment variable
    :rtype: str
    """
    # Use the (last) named option of the parameter and designate it
    # as a valid environment variable.
    long_options = [opt for opt in option_strings if opt[0:2] == "--"]
    return f"TID_{long_options[-1][2:].upper()}"


def process_environment_variables(parser: ArgumentParser) -> None:
    """Manipulate the actual commandline to insert environment options.

    The actual "sys.argv" is manipulated to enter values from environment
    variables, unless already present as commandline parameter.

    Perhaps not a beautifully solution, but does exactly what is required.

    :param parser: the ArgumentParser which contains all the parameters
    :type parser: ArgumentParser
    """
    for action in parser._actions:
        option_strings = action.option_strings
        env_var = deduce_environment_variable(option_strings)
        if env_var and use_env_variables(env_var, option_strings):
            # Specifically (only!) support our use-cases!
            # https://docs.python.org/3/library/argparse.html#nargs
            if action.nargs is None:
                sys.argv.append(option_strings[-1])
                sys.argv.append(os.environ[env_var])

            # if action.nargs == 0:
            #     # Only support "store_true" behavior
            #     if os.environ[env_var].lower() not in ("false", "0"):
            #         sys.argv.append(option_strings[-1])

            if action.nargs == "?":
                # Only support "store_true" behavior
                # environment variable will only be ignored
                # if set to false
                if os.environ[env_var].lower() not in ("false", "0"):
                    sys.argv.append(option_strings[-1])
                    # Set to true, will only activate,
                    # Anything other then true will be used as
                    # parameter value
                    if os.environ[env_var].lower() not in ("true", "1"):
                        sys.argv.append(os.environ[env_var])
