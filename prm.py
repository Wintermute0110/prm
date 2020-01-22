#!/usr/bin/python3 -B

#
# Python ROM Manager for No-Intro ROM sets.
#

# Copyright (c) 2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Python standard library --------------------------------------------------------------------
import argparse
import pprint
import sys

# --- PRM modules --------------------------------------------------------------------------------
import common
from common import log_error, log_warn, log_info, log_verb, log_debug

# --- Class with program options and settings ----------------------------------------------------
class Options:
    def __init__(self):
        self.config_file_name = 'configuration.xml'

# Process the program options in variable args. Returns an Options object.
def process_arguments(args):
    options = Options()
    if args.verbose:
        if args.verbose == 1:
            common.change_log_level(common.LOG_VERB)
            log_info('Verbosity level set to VERBOSE')
        elif args.verbose == 2:
            common.change_log_level(common.LOG_DEBUG)
            log_info('Verbosity level set to DEBUG')
    if args.dryRun:
        __prog_option_dry_run = 1

    return options

# Returns the configuration filter object given the filter name.
# Abort if not found.
def get_Filter_from_Config(filterName):
    if filterName in configuration.filters:
        return configuration.filters[filterName]
    log_error('Filter "{}" not found in configuration file'.format(filterName))
    sys.exit(20)

# --- Main body functions ------------------------------------------------------------------------
list_ljust = 16
def command_listcollections(options):
    log_info('\033[1m[Listing ROM Collections in the configuration file]\033[0m')

    # Read the configuration file.
    configuration = common.parse_File_Config(options)
    # pprint.pprint(configuration.collections)

    # Print the ROM Collections in the configuration file.
    # Use the table printing engine from AML/AEL.
    table_str = [
        ['left', 'left', 'left', 'left'],
        ['Name', 'Platform', 'DAT file', 'ROM dir'],
    ]
    for key in configuration.collections:
        collection = configuration.collections[key]
        table_str.append([
            collection['name'],
            collection['platform'],
            collection['DAT'],
            collection['ROM_dir'],
        ])

    # Print table
    table_text = common.text_render_table(table_str)
    print('')
    for line in table_text: print(line)

def command_usage():
  print("""\033[32mUsage: prm.py [options] COMMAND [COLLECTION]\033[0m

\033[32mCommands:\033[0m
\033[31musage\033[0m                    Print usage information (this text).
\033[31mlistcollections\033[0m          Display ROM collections in the configuration file.

\033[32mOptions:
\033[35m-h\033[0m, \033[35m--help\033[0m               Print short command reference.
\033[35m-v\033[0m, \033[35m--verbose\033[0m            Print more information about what's going on.
\033[35m--dryRun\033[0m                 Don't modify any files, just print the operations to be done.
""")

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
print('\033[36mPython ROM Manager for No-Intro ROM sets\033[0m version ' + common.PRM_VERSION)

# --- Command line parser
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help = "be verbose", action = "count")
parser.add_argument('--dryRun', help = "don't modify any files", action = "store_true")
parser.add_argument('command', help = "Main action to do", nargs = 1)
parser.add_argument("collection", help = "ROM collection name", nargs = '?')
args = parser.parse_args()
options = process_arguments(args)

# --- Positional arguments that don't require a filterName
command = args.command[0]
if command == 'usage':
    command_usage(options)
elif command == 'listcollections':
    command_listcollections(options)
else:
    print('\033[31m[ERROR]\033[0m Unrecognised command "{}"'.format(command))
    sys.exit(1)

# Sayonara
sys.exit(0)
