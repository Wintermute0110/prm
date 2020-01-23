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
from common import FileName

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
def command_listcollections(options):
    log_info('\033[1mListing ROM Collections in the configuration file\033[0m')

    # Read the configuration file.
    configuration = common.parse_File_Config(options)
    # pprint.pprint(configuration.collections)

    # Print the ROM Collections in the configuration file.
    # Use the table printing engine from AML/AEL.
    table_str = [
        ['left', 'left', 'left'],
        ['Name', 'DAT file', 'ROM dir'],
    ]
    for key in configuration.collections:
        collection = configuration.collections[key]
        table_str.append([collection['name'], collection['DAT'], collection['ROM_dir']])

    # Print table
    table_text = common.text_render_table(table_str)
    print('')
    for line in table_text: print(line)

def command_scan(options, collection_name):
    log_info('\033[1mScanning collection\033[0m')
    configuration = common.parse_File_Config(options)

    # Check if the configuration in the command line exists.
    if collection_name not in configuration.collections:
        log_error('Collection "{}" not found in the configuration file.'.format(collection_name))
        sys.exit(1)
    collection = configuration.collections[collection_name]

    # Load DAT file.
    DAT_FN = FileName(collection['DAT'])
    DAT = common.load_XML_DAT_file(DAT_FN)

    # Scan files in ROM_dir.
    ROM_dir_FN = FileName(collection['ROM_dir'])
    log_info('Scanning files in "{}"...'.format(ROM_dir_FN.getPath()))
    if not ROM_dir_FN.exists():
        log_error('Directory does not exist "{}"'.format(ROM_dir_FN.getPath()))
        sys.exit(10)
    file_list = ROM_dir_FN.recursiveScanFilesInPath('*')

    # Process files.
    set_list = []
    for filename in sorted(file_list):
        # Determine status of the ROM set (aka ZIP file).
        set = common.get_ROM_set_status(filename, DAT)
        set_list.append(set)

    # Print scanner results.
    for set in set_list:
        log_info('SET {} "{}"'.format(set.status, set.filename))
        for rom in set.rom_list:
            if rom['status'] == common.ROMset.ROM_STATUS_BADNAME:
                log_info('ROM {} "{}" -> "{}"'.format(
                    rom['status'], rom['name'], rom['correct_rom_name']))
            else:
                log_info('ROM {} "{}"'.format(rom['status'], rom['name']))

def command_fix(options, collection_name):
    log_info('\033[1mFixing collection\033[0m')
    configuration = common.parse_File_Config(options)

    # Check if the configuration in the command line exists.
    if collection_name not in configuration.collections:
        log_error('Collection "{}" not found in the configuration file.'.format(collection_name))
        sys.exit(1)
    collection = configuration.collections[collection_name]

    # Load DAT file.
    DAT_FN = FileName(collection['DAT'])
    DAT = common.load_XML_DAT_file(DAT_FN)

    # Scan files in ROM_dir.
    ROM_dir_FN = FileName(collection['ROM_dir'])
    log_info('Scanning files in "{}"...'.format(ROM_dir_FN.getPath()))
    if not ROM_dir_FN.exists():
        log_error('Directory does not exist "{}"'.format(ROM_dir_FN.getPath()))
        sys.exit(10)
    file_list = ROM_dir_FN.recursiveScanFilesInPath('*')

    # Process files.
    set_list = []
    for filename in sorted(file_list):
        # Determine status of the ROM set (aka ZIP file).
        set = common.get_ROM_set_status(filename)
        set_list.append(set)

    # Compute statistics.

    # Fix sets.
    for set in set_list:
        if set.status == common.ROMset.SET_STATUS_BADNAME:
            common.fix_ROM_set(set)

def command_usage():
  print("""\033[32mUsage: prm.py [options] COMMAND [COLLECTION]\033[0m

\033[32mCommands:\033[0m
\033[31musage\033[0m                    Print usage information (this text).
\033[31mlistcollections\033[0m          Display ROM collections in the configuration file.
\033[31mscan COLLECTION\033[0m          Scan ROM_dir in a collection and print results.
\033[31mfix COLLECTION\033[0m           Fixes sets in ROM_dir in a collection.

\033[32mOptions:
\033[35m-h\033[0m, \033[35m--help\033[0m               Print short command reference.
\033[35m-v\033[0m, \033[35m--verbose\033[0m            Print more information about what's going on.
\033[35m--dryRun\033[0m                 Don't modify any files, just print the operations to be done.
""")

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
print('\033[36mPython ROM Manager for No-Intro ROM sets\033[0m version ' + common.PRM_VERSION)

# --- Initialise data directory
# This is used to store the results of scans for later display. Use JSON to store data.

# --- Command line parser
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help = 'Bbe verbose', action = 'count')
parser.add_argument('--dryRun', help = 'Do not modify any files', action = 'store_true')
parser.add_argument('command', help = 'Main action to do', nargs = 1)
parser.add_argument('collection', help = 'ROM collection name', nargs = '?')
args = parser.parse_args()
options = process_arguments(args)
# pprint.pprint(args)

# --- Positional arguments that don't require a filterName
command = args.command[0]
if command == 'usage':
    command_usage()
elif command == 'listcollections':
    command_listcollections(options)
elif command == 'scan':
    collection_name = args.collection
    command_scan(options, collection_name)
elif command == 'fix':
    collection_name = args.collection
    command_fix(options, collection_name)
else:
    print('\033[31m[ERROR]\033[0m Unrecognised command "{}"'.format(command))
    sys.exit(1)

# Sayonara
sys.exit(0)
