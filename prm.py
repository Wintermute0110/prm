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
import os
import pickle
import pprint
import sys

# --- PRM modules --------------------------------------------------------------------------------
import common
from common import log_error, log_warn, log_info, log_verb, log_debug
from common import FileName
from common import ROMcollection

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

def perform_scanner(configuration, collection_name):
    log_info('***** Scanning collection {} *****'.format(collection_name))
    if collection_name not in configuration.collections:
        log_error('Collection "{}" not found in the configuration file.'.format(collection_name))
        sys.exit(1)
    collection_conf = configuration.collections[collection_name]

    # Load DAT file.
    DAT_dir_FN = FileName(configuration.common_opts['NoIntro_DAT_dir'])
    DAT_FN = DAT_dir_FN.pjoin(collection_conf['DAT'])
    DAT = common.load_XML_DAT_file(DAT_FN)

    # Scan files in ROM_dir.
    collection = ROMcollection(collection_conf )
    collection.scan_files_in_dir()
    collection.process_files(DAT)

    return collection

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
    collection = perform_scanner(configuration, collection_name)
    # Save scanner results for later.
    scan_FN = options.data_dir_FN.pjoin(collection.name + '_scan.bin')
    print('Saving scanner results in "{}"'.format(scan_FN.getPath()))
    f = open(scan_FN.getPath(), 'wb')
    pickle.dump(collection, f)
    f.close()

    # Print scanner summary.
    stats = common.get_collection_statistics(collection)
    print('\n=== Scanner summary for collection "{}" ==='.format(collection_name))
    print('Total SETs in DAT {:5,}'.format(stats['total_DAT']))
    print('Total SETs        {:5,}'.format(stats['total']))
    print('Have SETs         {:5,}'.format(stats['have']))
    print('Badname SETs      {:5,}'.format(stats['badname']))
    print('Miss SETs         {:5,}'.format(stats['missing']))
    print('Unknown SETs      {:5,}'.format(stats['unknown']))
    print('Error SETs        {:5,}'.format(stats['error']))

def command_scanall(options):
    log_info('Scanning all collections')
    configuration = common.parse_File_Config(options)

    # Scan collection by collection.
    stats_list = []
    for collection_name in configuration.collections:
        collection = perform_scanner(configuration, collection_name)
        # Save scanner results for later.
        scan_FN = options.data_dir_FN.pjoin(collection.name + '_scan.bin')
        print('Saving scanner results in "{}"'.format(scan_FN.getPath()))
        f = open(scan_FN.getPath(), 'wb')
        pickle.dump(collection, f)
        f.close()

def command_status(options, collection_name):
    log_info('View collection scan results')
    # Load collection scanner data.
    scan_FN = options.data_dir_FN.pjoin(collection_name + '_scan.bin')
    if not scan_FN.exists():
        print('Not found {}'.format(scan_FN.getPath()))
        print('Exiting')
        sys.exit(1)
    print('Loading scanner results in "{}"'.format(scan_FN.getPath()))
    f = open(scan_FN.getPath(), 'rb')
    collection = pickle.load(f)
    f.close()

    # Print scanner summary.
    stats = common.get_collection_statistics(collection)
    print('\n=== Scanner summary for collection "{}" ==='.format(collection_name))
    print('Total SETs in DAT {:5,}'.format(stats['total_DAT']))
    print('Total SETs        {:5,}'.format(stats['total']))
    print('Have SETs         {:5,}'.format(stats['have']))
    print('Badname SETs      {:5,}'.format(stats['badname']))
    print('Miss SETs         {:5,}'.format(stats['missing']))
    print('Unknown SETs      {:5,}'.format(stats['unknown']))
    print('Error SETs        {:5,}'.format(stats['error']))

def command_statusall(options):
    log_info('View all collections scan results')
    configuration = common.parse_File_Config(options)

    stats_list = []
    for collection_name in configuration.collections:
        # Load collection scanner data.
        scan_FN = options.data_dir_FN.pjoin(collection_name + '_scan.bin')
        if not scan_FN.exists():
            print('Not found {}'.format(scan_FN.getPath()))
            print('Exiting')
            sys.exit(1)
        print('Loading scanner results in "{}"'.format(scan_FN.getPath()))
        f = open(scan_FN.getPath(), 'rb')
        collection = pickle.load(f)
        f.close()
        stats = common.get_collection_statistics(collection)
        stats_list.append(stats)

    # Print results.
    table_str = [
        ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'],
        ['Collection', 'DAT SETs', 'Total ROMs', 'Have ROMs',
         'BadName ROMs', 'Miss ROMs', 'Unknown ROMs', 'Error files'],
    ]
    for stats in stats_list:
        table_str.append([
            str(stats['name']), str(stats['total_DAT']), str(stats['total']), str(stats['have']),
            str(stats['badname']), str(stats['missing']), str(stats['unknown']), str(stats['error']),
        ])
    table_text = common.text_render_table(table_str)
    print('')
    for line in table_text: print(line)

def command_listROMs(options, collection_name):
    log_info('List collection scanned ROMs')
    # Load collection scanner data.
    scan_FN = options.data_dir_FN.pjoin(collection_name + '_scan.bin')
    if not scan_FN.exists():
        print('Not found {}'.format(scan_FN.getPath()))
        print('Exiting')
        sys.exit(1)
    print('Loading scanner results in "{}"'.format(scan_FN.getPath()))
    f = open(scan_FN.getPath(), 'rb')
    collection = pickle.load(f)
    f.close()

    # Print scanner results (long list)
    print('\n=== Scanner long list ===')
    for set in collection.sets:
        log_info('\033[91mSET\033[0m {} "{}"'.format(set.status, set.basename))
        for rom in set.rom_list:
            if rom['status'] == common.ROMset.ROM_STATUS_BADNAME:
                log_info('ROM {} "{}" -> "{}"'.format(
                    rom['status'], rom['name'], rom['correct_name']))
            else:
                log_info('ROM {} "{}"'.format(rom['status'], rom['name']))

def command_listIssues(options, collection_name):
    log_info('List collection scanned ROMs with issues')
    # Load collection scanner data.
    scan_FN = options.data_dir_FN.pjoin(collection_name + '_scan.bin')
    if not scan_FN.exists():
        print('Not found {}'.format(scan_FN.getPath()))
        print('Exiting')
        sys.exit(1)
    print('Loading scanner results in "{}"'.format(scan_FN.getPath()))
    f = open(scan_FN.getPath(), 'rb')
    collection = pickle.load(f)
    f.close()

    # Print scanner results (long list)
    print('\n=== Scanner long list ===')
    for set in collection.sets:
        if set.status == common.ROMset.SET_STATUS_GOOD: continue
        log_info('\033[91mSET\033[0m {} "{}"'.format(set.status, set.basename))
        for rom in set.rom_list:
            if rom['status'] == common.ROMset.ROM_STATUS_BADNAME:
                log_info('ROM {} "{}" -> "{}"'.format(
                    rom['status'], rom['name'], rom['correct_name']))
            else:
                log_info('ROM {} "{}"'.format(rom['status'], rom['name']))

LIST_BADNAME = 100
LIST_MISSING = 200
LIST_UNKNOWN = 300
LIST_ERROR   = 400
def command_listStuff(options, collection_name, list_type):
    log_info('List collection scanned ROMs with issues')
    # Load collection scanner data.
    scan_FN = options.data_dir_FN.pjoin(collection_name + '_scan.bin')
    if not scan_FN.exists():
        print('Not found {}'.format(scan_FN.getPath()))
        print('Exiting')
        sys.exit(1)
    print('Loading scanner results in "{}"'.format(scan_FN.getPath()))
    f = open(scan_FN.getPath(), 'rb')
    collection = pickle.load(f)
    f.close()

    # Print scanner results (long list)
    print('\n=== Scanner long list ===')
    num_items = 0
    for set in collection.sets:
        # Filter SET
        if list_type == LIST_BADNAME:
            if set.status != common.ROMset.SET_STATUS_BADNAME: continue
        elif list_type == LIST_MISSING:
            if set.status != common.ROMset.SET_STATUS_MISSING: continue
        elif list_type == LIST_UNKNOWN:
            if set.status != common.ROMset.SET_STATUS_UNKNOWN: continue
        elif list_type == LIST_ERROR:
            if set.status != common.ROMset.SET_STATUS_ERROR: continue
        else:
            raise TypeError('Wrong type. Logical error.')

        log_info('\033[91mSET\033[0m {} "{}"'.format(set.status, set.basename))
        num_items += 1
        for rom in set.rom_list:
            if rom['status'] == common.ROMset.ROM_STATUS_BADNAME:
                log_info('ROM {} "{}" -> "{}"'.format(
                    rom['status'], rom['name'], rom['correct_name']))
            else:
                log_info('ROM {} "{}"'.format(rom['status'], rom['name']))
    print('\nListed {} items.'.format(num_items))

def command_fix(options, collection_name):
    log_info('Fixing collection {}'.format(collection_name))
    configuration = common.parse_File_Config(options)
    collection = perform_scanner(configuration, collection_name)
    for set in collection.sets:
        if set.status == common.ROMset.SET_STATUS_BADNAME:
            common.fix_ROM_set(set)
    # Rescan collection and store results in chache.
    command_scan(options, collection_name)

def command_deleteUnknown(options, collection_name):
    log_info('Deleting Unknown SETs in collection {}'.format(collection_name))
    configuration = common.parse_File_Config(options)
    collection = perform_scanner(configuration, collection_name)
    for set in collection.sets:
        if set.status == common.ROMset.SET_STATUS_UNKNOWN:
            print('Deleting {}'.format(set.basename))
            os.remove(set.filename)
    # Rescan collection and store results in chache.
    command_scan(options, collection_name)

def command_usage():
  print("""Usage: prm.py [options] COMMAND [COLLECTION]

Commands:
usage                     Print usage information (this text).
list                      Display ROM collections in the configuration file.
scan COLLECTION           Scan ROM_dir in a collection and print results.
scanall                   Scan all the collections.
status COLLECTION         View scanner results.
statusall                 View scanner results for all collections.

listROMs COLLECTION       List SETs of a collection with status.
listIssues COLLECTION     List SETs with issues (BadName, Missing, Unknown, Error).
listBadName
listMissing
listUnknown
listError

fix COLLECTION            Fixes sets in ROM_dir in a collection.

deleteUnknown COLLECTION  Delete Unknown ROMs.

Options:
-h, --help                Print short command reference.
-v, --verbose             Print more information about what's going on.
--dryRun                  Don't modify any files, just print the operations to be done.""")

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
print('\033[36mPython ROM Manager for No-Intro ROM sets\033[0m version ' + common.PRM_VERSION)

# --- Initialise data and temp directories
# This is used to store the results of scans for later display. Use JSON to store data.
this_FN = FileName(__file__)
data_dir_FN = FileName(this_FN.getDir()).pjoin('data')
temp_dir_FN = FileName(this_FN.getDir()).pjoin('tmp')
log_info('Data dir "{}"'.format(data_dir_FN.getPath()))
log_info('Temp dir "{}"'.format(temp_dir_FN.getPath()))

# --- Command line parser
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help = 'Bbe verbose', action = 'count')
parser.add_argument('--dryRun', help = 'Do not modify any files', action = 'store_true')
parser.add_argument('command', help = 'Main action to do', nargs = 1)
parser.add_argument('collection', help = 'ROM collection name', nargs = '?')
args = parser.parse_args()
options = process_arguments(args)
options.data_dir_FN = data_dir_FN
options.temp_dir_FN = temp_dir_FN
# pprint.pprint(args)

# --- Positional arguments that don't require a filterName
command = args.command[0]
if command == 'usage': command_usage()
elif command == 'list': command_listcollections(options)

elif command == 'scan': command_scan(options, args.collection)
elif command == 'scanall': command_scanall(options)

elif command == 'status': command_status(options, args.collection)
elif command == 'statusall': command_statusall(options)

elif command == 'listROMs': command_listROMs(options, args.collection)
elif command == 'listIssues': command_listIssues(options, args.collection)
elif command == 'listBadName': command_listStuff(options, args.collection, LIST_BADNAME)
elif command == 'listMissing': command_listStuff(options, args.collection, LIST_MISSING)
elif command == 'listUnknown': command_listStuff(options, args.collection, LIST_UNKNOWN)
elif command == 'listError': command_listStuff(options, args.collection, LIST_ERROR)

elif command == 'fix': command_fix(options, args.collection)
elif command == 'deleteUnknown': command_deleteUnknown(options, args.collection)

else:
    print('\033[31m[ERROR]\033[0m Unrecognised command "{}"'.format(command))
    sys.exit(1)

# Sayonara
sys.exit(0)
