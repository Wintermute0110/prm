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

def perform_scanner(collection):
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

    return set_list

# --- Main body functions ------------------------------------------------------------------------
def command_listcollections(options):
    log_info('Listing ROM Collections in the configuration file')

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
    log_info('Scanning collection')
    configuration = common.parse_File_Config(options)

    # Check if the configuration in the command line exists and do scanning.
    if collection_name not in configuration.collections:
        log_error('Collection "{}" not found in the configuration file.'.format(collection_name))
        sys.exit(1)
    collection = configuration.collections[collection_name]
    set_list = perform_scanner(collection)

    # Print scanner results (long list)
    print('\n=== Scanner long list ===')
    for set in set_list:
        log_info('SET {} "{}"'.format(set.status, set.filename))
        for rom in set.rom_list:
            if rom['status'] == common.ROMset.ROM_STATUS_BADNAME:
                log_info('ROM {} "{}" -> "{}"'.format(
                    rom['status'], rom['name'], rom['correct_name']))
            else:
                log_info('ROM {} "{}"'.format(rom['status'], rom['name']))

    # Print scanner summary.
    stats = common.get_collection_statistics(set_list)
    print('\n=== Scanner results ===')
    print('Collection   {}'.format(collection_name))
    print('Total ROMs   {:,}'.format(stats['total']))
    print('Have ROMs    {:,}'.format(stats['have']))
    print('Miss ROMs    {:,}'.format(stats['miss']))
    print('Badname ROMs {:,}'.format(stats['badname']))
    print('Unknown ROMs {:,}'.format(stats['unknown']))

def command_scanall(options):
    log_info('Scanning collection')
    configuration = common.parse_File_Config(options)

    # Scan collection by collection.
    stats_list = []
    for collection_name in configuration.collections:
        collection = configuration.collections[collection_name]
        set_list = perform_scanner(collection)
        stats = common.get_collection_statistics(set_list)
        stats['name'] = collection_name
        stats_list.append(stats)

    # Print results.
    table_str = [
        ['left', 'left', 'left', 'left', 'left', 'left'],
        ['Collection', 'Total ROMs', 'Have ROMs', 'Miss ROMs', 'BadName ROMs', 'Unknown ROMs'],
    ]
    for stats in stats_list:
        table_str.append([
            str(stats['name']), str(stats['total']), str(stats['have']),
            str(stats['miss']), str(stats['badname']), str(stats['unknown']),
        ])
    table_text = common.text_render_table(table_str)
    print('')
    for line in table_text: print(line)

def command_fix(options, collection_name):
    log_info('Fixing collection')
    configuration = common.parse_File_Config(options)

    # Check if the configuration in the command line exists and do scanning.
    if collection_name not in configuration.collections:
        log_error('Collection "{}" not found in the configuration file.'.format(collection_name))
        sys.exit(1)
    collection = configuration.collections[collection_name]
    set_list = perform_scanner(collection)

    # Fix sets.
    for set in set_list:
        if set.status == common.ROMset.SET_STATUS_BAD:
            common.fix_ROM_set(set)

def command_usage():
  print("""Usage: prm.py [options] COMMAND [COLLECTION]

Commands:
usage                    Print usage information (this text).
listcollections          Display ROM collections in the configuration file.
scan COLLECTION          Scan ROM_dir in a collection and print results.
scanall                  Scan all the collections.
fix COLLECTION           Fixes sets in ROM_dir in a collection.

Options:
-h, --help               Print short command reference.
-v, --verbose            Print more information about what's going on.
--dryRun                 Don't modify any files, just print the operations to be done.""")

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
elif command == 'scanall':
    command_scanall(options)
elif command == 'fix':
    collection_name = args.collection
    command_fix(options, collection_name)
else:
    print('\033[31m[ERROR]\033[0m Unrecognised command "{}"'.format(command))
    sys.exit(1)

# Sayonara
sys.exit(0)
