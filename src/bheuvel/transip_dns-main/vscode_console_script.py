#!/usr/local/bin/python
# -*- coding: utf-8 -*-
"""Startup script to be used by VSCode.

VSCode does not support the concept of console scripts, or entry points:

https://python-packaging.readthedocs.io/en/latest/command-line-scripts.html#the-console-scripts-entry-point

This file is a copy of the actual implementation of such a console script.
When running/debugging the script, use this file in your ".vscode/launch.json":
    "configurations": [
    {
        "program": "${workspaceFolder}/vscode_console_script.py"
    ...
"""
import re
import sys
from transip_dns.transip_dns import main

if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
