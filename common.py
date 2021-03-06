#!/usr/bin/python3 -B

#
# Python ROM Manager. Common Python module for prm and prm-mame.
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
from collections import OrderedDict
import hashlib
import fnmatch
import os
import pprint
import re
import sys
import xml.etree.ElementTree
import zipfile
import zlib

# --- Global variables ---------------------------------------------------------------------------
PRM_VERSION = '0.1.0'

# --- DEBUG functions ----------------------------------------------------------------------------
def debug_dumpclean(obj):
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
               print(k)
               dumpclean(v)
        else:
             print('%s : %s' % (k, v))
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                print(v)
    else:
        print(obj)

# --- Logging functions --------------------------------------------------------------------------
LOG_ERROR = 1
LOG_WARN  = 2
LOG_INFO  = 3
LOG_VERB  = 4
LOG_DEBUG = 5
f_log = None           # Log file object
log_level = LOG_INFO   # Log level
file_log_flag = False  # User wants file log

def init_log_system(prog_option_file_log):
    global file_log_flag
    global f_log

    file_log_flag = prog_option_file_log

    # --- Open log file descriptor
    if file_log_flag and f_log is None:
        f_log = open(__prog_option_log_filename, 'w')

def change_log_level(level):
    global log_level

    log_level = level

# --- Print/log to a specific level
def myprint(level, print_str):
    # --- Write to console depending on verbosity
    if level <= log_level:
        print(print_str)

    # --- Write to file
    if file_log_flag and level <= log_level:
        if print_str[-1] != '\n': print_str += '\n'
        f_log.write(print_str) # python will convert \n to os.linesep

# --- Some useful function overloads
def log_error(print_str): myprint(LOG_ERROR, print_str)

def log_warn(print_str): myprint(LOG_WARN, print_str)

def log_info(print_str): myprint(LOG_INFO, print_str)

def log_verb(print_str): myprint(LOG_VERB, print_str)

def log_debug(print_str): myprint(LOG_DEBUG, print_str)

# --- XML functions ------------------------------------------------------------------------------
# Reads merged MAME XML file.
# Returns an ElementTree object.
# Aborts if errors found.
def XML_read_file_ElementTree(filename):
    print('Reading XML file "{}"... '.format(filename), end = '')
    sys.stdout.flush()
    if not os.path.isfile(filename):
        print('\n\033[31m[ERROR]\033[0m File \'{0}\' not found'.format(filename))
        sys.exit(1)
    try:
        tree = xml.etree.ElementTree.parse(filename)
    except IOError:
        print('\n\033[31m[ERROR]\033[0m Cannot find file \'{0}\''.format(filename))
        sys.exit(1)
    print('done')
    sys.stdout.flush()

    return tree

def text_unescape_XML(data_str):
    data_str = data_str.replace('&quot;', '"')
    data_str = data_str.replace('&apos;', "'")

    data_str = data_str.replace('&lt;', '<')
    data_str = data_str.replace('&gt;', '>')
    # Ampersand MUST BE replaced LAST
    data_str = data_str.replace('&amp;', '&')

    # --- Unprintable characters ---
    data_str = data_str.replace('&#10;', '\n')
    data_str = data_str.replace('&#13;', '\r')
    data_str = data_str.replace('&#9;', '\t')

    return data_str

# Returns a list of strings that must be joined with '\n'.join()
#
# First row            column aligment 'right' or 'left'
# Second row           column titles
# Third and next rows  table data
#
# Input:
# table_str = [
#     ['left', 'left', 'left'],
#     ['Platform', 'Parents', 'Clones'],
#     ['', '', ''],
# ]
#
# Output:
#
def text_render_table(table_str, trim_Kodi_colours = False):
    rows = len(table_str)
    cols = len(table_str[0])

    # Remove Kodi tags [COLOR string] and [/COLOR]
    if trim_Kodi_colours:
        new_table_str = []
        for i in range(rows):
            new_table_str.append([])
            for j in range(cols):
                s = text_remove_Kodi_color_tags(table_str[i][j])
                new_table_str[i].append(s)
        table_str = new_table_str

    # Determine sizes and padding.
    # Ignore row 0 when computing sizes.
    table_str_list = []
    col_sizes = text_get_table_str_col_sizes(table_str, rows, cols)
    col_padding = table_str[0]

    # --- Table header ---
    row_str = ''
    for j in range(cols):
        if j < cols - 1:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j]) + '  '
        else:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j])
    table_str_list.append(row_str)
    # Table line -----
    total_size = sum(col_sizes) + 2*(cols-1)
    table_str_list.append('{0}'.format('-' * total_size))

    # --- Data rows ---
    for i in range(2, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j]) + '  '
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j]) + '  '
            else:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j])
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j])
        table_str_list.append(row_str)

    return table_str_list

# Removed Kodi colour tags before computing size (substitute by ''):
#   A) [COLOR skyblue]
#   B) [/COLOR]
def text_get_table_str_col_sizes(table_str, rows, cols):
    col_sizes = [0] * cols
    for j in range(cols):
        col_max_size = 0
        for i in range(1, rows):
            cell_str = re.sub(r'\[COLOR \w+?\]', '', table_str[i][j])
            cell_str = re.sub(r'\[/COLOR\]', '', cell_str)
            str_size = len('{0}'.format(cell_str))
            if str_size > col_max_size: col_max_size = str_size
        col_sizes[j] = col_max_size

    return col_sizes

def text_print_padded_left(str, str_max_size):
    formatted_str = '{0}'.format(str)
    padded_str =  formatted_str + ' ' * (str_max_size - len(formatted_str))

    return padded_str

def text_print_padded_right(str, str_max_size):
    formatted_str = '{0}'.format(str)
    padded_str = ' ' * (str_max_size - len(formatted_str)) + formatted_str

    return padded_str

# -------------------------------------------------------------------------------------------------
# Filesystem helper class
# This class always takes and returns Unicode string paths. Decoding to UTF-8 must be done in
# caller code.
# A) Transform paths like smb://server/directory/ into \\server\directory\
# B) Use xbmc.translatePath() for paths starting with special://
# -------------------------------------------------------------------------------------------------
class FileName:
    # pathString must be a Unicode string object
    def __init__(self, pathString):
        self.originalPath = pathString
        self.path         = pathString
        
        # --- Path transformation ---
        if self.originalPath.lower().startswith('smb:'):
            self.path = self.path.replace('smb:', '')
            self.path = self.path.replace('SMB:', '')
            self.path = self.path.replace('//', '\\\\')
            self.path = self.path.replace('/', '\\')

        elif self.originalPath.lower().startswith('special:'):
            self.path = xbmc.translatePath(self.path)

    def _join_raw(self, arg):
        self.path         = os.path.join(self.path, arg)
        self.originalPath = os.path.join(self.originalPath, arg)

        return self

    # Appends a string to path. Returns self FileName object
    def append(self, arg):
        self.path         = self.path + arg
        self.originalPath = self.originalPath + arg

        return self

    # >> Joins paths. Returns a new FileName object
    def pjoin(self, *args):
        child = FileName(self.originalPath)
        for arg in args:
            child._join_raw(arg)

        return child

    # Behaves like os.path.join()
    #
    # See http://blog.teamtreehouse.com/operator-overloading-python
    # other is a FileName object. other originalPath is expected to be a subdirectory (path
    # transformation not required)
    def __add__(self, other):
        current_path = self.originalPath
        if type(other) is FileName:  other_path = other.originalPath
        elif type(other) is unicode: other_path = other
        elif type(other) is str:     other_path = other.decode('utf-8')
        else: raise NameError('Unknown type for overloaded + in FileName object')
        new_path = os.path.join(current_path, other_path)
        child    = FileName(new_path)

        return child

    def escapeQuotes(self):
        self.path = self.path.replace("'", "\\'")
        self.path = self.path.replace('"', '\\"')

    # ---------------------------------------------------------------------------------------------
    # Decomposes a file name path or directory into its constituents
    #   FileName.getOriginalPath()  Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath()          Full path                                     /home/Wintermute/Sonic.zip
    #   FileName.getPath_noext()    Full path with no extension                   /home/Wintermute/Sonic
    #   FileName.getDir()           Directory name of file. Does not end in '/'   /home/Wintermute/
    #   FileName.getBase()          File name with no path                        Sonic.zip
    #   FileName.getBase_noext()    File name with no path and no extension       Sonic
    #   FileName.getExt()           File extension                                .zip
    # ---------------------------------------------------------------------------------------------
    def getOriginalPath(self):
        return self.originalPath

    def getPath(self):
        return self.path

    def getPath_noext(self):
        root, ext = os.path.splitext(self.path)

        return root

    def getDir(self):
        return os.path.dirname(self.path)

    def getBase(self):
        return os.path.basename(self.path)

    def getBase_noext(self):
        basename  = os.path.basename(self.path)
        root, ext = os.path.splitext(basename)
        
        return root

    def getExt(self):
        root, ext = os.path.splitext(self.path)
        
        return ext

    # ---------------------------------------------------------------------------------------------
    # Scanner functions
    # ---------------------------------------------------------------------------------------------
    def scanFilesInPath(self, mask):
        files = []
        filenames = os.listdir(self.path)
        for filename in fnmatch.filter(filenames, mask):
            files.append(os.path.join(self.path, filename))

        return files

    def scanFilesInPathAsPaths(self, mask):
        files = []
        filenames = os.listdir(self.path)
        for filename in fnmatch.filter(filenames, mask):
            files.append(FileName(os.path.join(self.path, filename)))

        return files

    def recursiveScanFilesInPath(self, mask):
        files = []
        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                files.append(os.path.join(root, filename))

        return files

    # ---------------------------------------------------------------------------------------------
    # Filesystem functions
    # ---------------------------------------------------------------------------------------------
    def stat(self):
        return os.stat(self.path)

    def exists(self):
        return os.path.exists(self.path)

    def isdir(self):
        return os.path.isdir(self.path)
        
    def isfile(self):
        return os.path.isfile(self.path)

    def makedirs(self):
        if not os.path.exists(self.path): 
            os.makedirs(self.path)

    # os.remove() and os.unlink() are exactly the same.
    def unlink(self):
        os.unlink(self.path)

    def rename(self, to):
        os.rename(self.path, to.getPath())

# --- Configuration file stuff --------------------------------------------------------------------
class ConfigFile:
    # Valid tags in the XML file. Text in these tags is string.
    common_tag_set = [
        'NoIntro_DAT_dir',
        'NoIntro_pclone_DAT_dir',
        'MAME_DAT_dir',
        'Incoming_dir',
    ]
    collection_tag_set = [
        'name',
        'platform',
        'HeaderOffset',
        'HeaderRule',
        'DAT',
        'ROM_dir',
    ]

    def __init__(self):
        # Dictionary of strings. Key is the XML tag name in <common>.
        # Uses OrderedDict() to keep order as found in the config file.
        self.common_opts = OrderedDict([
            ('NoIntro_DAT_dir', ''),
            ('NoIntro_pclone_DAT_dir', ''),
            ('MAME_DAT_dir', ''),
            ('Incoming_dir', ''),
        ])

        # Dictionary of dictionaries. Key is the collection name.
        # Uses OrderedDict() to keep order as found in the config file.
        self.collections = OrderedDict()

    def new_collection_dic(self):
        return OrderedDict([
            ('name', ''),
            ('platform', ''),
            ('HeaderOffset', 0),
            ('HeaderRules', []),
            ('DAT', ''),
            ('ROM_dir', ''),
        ])

# Parses configuration file using ElementTree.
# Returns a ConfigFile object
def parse_File_Config(options):
    log_info('Parsing configuration file')
    xml_tree = XML_read_file_ElementTree(options.config_file_name)
    xml_root = xml_tree.getroot()
    configuration = ConfigFile()
    for root_child in xml_root:
        if root_child.tag == 'common':
            for filter_child in root_child:
                # NARS.util_sanitize_dir_name(filter_child.text)
                xml_text = filter_child.text if filter_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = filter_child.tag
                if xml_tag not in ConfigFile.common_tag_set:
                    print('[ERROR] On <common> section')
                    print('[ERROR] Unrecognised tag <{}>'.format(xml_tag))
                    sys.exit(10)
                # Map tags to dictionary keys and text to dictionary values.
                # So far all text in the common section are strings.
                configuration.common_opts[xml_tag] = xml_text
        elif root_child.tag == 'collection':
            collection = configuration.new_collection_dic()
            for filter_child in root_child:
                xml_text = filter_child.text if filter_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                xml_tag  = filter_child.tag
                if xml_tag not in ConfigFile.collection_tag_set:
                    print('[ERROR] On <collection> section')
                    print('[ERROR] Unrecognised tag <{}>'.format(xml_tag))
                    sys.exit(10)
                # Convert data types if not string.
                # By default all tag context is string.
                if xml_tag == 'HeaderOffset':
                    collection[xml_tag] = int(xml_text)
                elif xml_tag == 'HeaderRule':
                    offset = int(filter_child.attrib['offset'])
                    collection['HeaderRules'].append({
                        'offset' : offset,
                        'value' : xml_text,
                    })
                else:
                    collection[xml_tag] = xml_text
            filter_name = collection['name']
            if not filter_name:
                    print('[ERROR] Collection has empty <name> tag.')
                    sys.exit(10)
            collection['name'] = filter_name
            configuration.collections[filter_name] = collection
            log_debug('Adding collection "{}"'.format(filter_name))
        else:
            log_error('[ERROR] At XML root level')
            log_error('[ERROR] Unrecognised tag <{}>'.format(root_child.tag))
            sys.exit(10)

    return configuration

# --- DAT file functions -------------------------------------------------------------------------
class DATfile:
    def __init__(self):
        # Key is crc, value is a tuple (a, b) a is the set index, b is the ROM index.
        self.crc_index = {}
        self.md5_index = {}
        self.sha1_index = {}
        self.sets = []

    def new_set(self):
        return {
            'name' : '',
            'cloneof' : '',
            'description' : '',
            'ROMs' : [],
        }

    def new_rom(self):
        return {
            'name' : '',
            'size' : 0,
            'crc' : '',
            'md5' : '',
            'sha1' : '',
        }

    def num_sets(self): return len(self.sets)

    def num_ROMs(self):
        num_ROMs = 0
        for set in self.sets:
            for ROM in set['ROMs']:
                num_ROMs += 1
        return num_ROMs

    def create_indices(self):
        for i, set in enumerate(self.sets):
            for j, ROM in enumerate(set['ROMs']):
                if ROM['crc'] in self.crc_index:
                    log_error('In set {} ROM {}'.format(set['name'], ROM['name']))
                    log_error('Duplicated CRC {}'.format(ROM['crc']))
                    sys.exit(2)
                if ROM['md5'] in self.md5_index:
                    log_error('In set {} ROM {}'.format(set['name'], ROM['name']))
                    log_error('Duplicated MD5 {}'.format(ROM['md5']))
                    sys.exit(2)
                if ROM['sha1'] in self.sha1_index:
                    log_error('In set {} ROM {}'.format(set['name'], ROM['name']))
                    log_error('Duplicated SHA1 {}'.format(ROM['sha1']))
                    sys.exit(2)
                self.crc_index[ROM['crc']] = (i, j)
                self.md5_index[ROM['md5']] = (i, j)
                self.sha1_index[ROM['sha1']] = (i, j)

    def ROM_CRC_exists(self, crc):
        return crc in self.crc_index

    def ROM_SHA1_exists(self, crc):
        return crc in self.sha1_index

    def get_ROM_CRC(self, crc):
        set_idx, rom_idx = self.crc_index[crc]
        return self.sets[set_idx]['ROMs'][rom_idx]

# Loads a No-Intro XML DAT file. DTD "http://www.logiqx.com/Dats/datafile.dtd"
# Checks that there are no duplicate CRCs in the DAT file, aborts if so.
# Returns a DATfile class.
def load_XML_DAT_file(xml_FN):
    if not xml_FN.exists():
        log_error('Does not exist "{0}"'.format(xml_FN.getPath()))
        sys.exit(10)

    # Parse using ElementTree
    log_info('Loading XML "{0}"'.format(xml_FN.getOriginalPath()))
    try:
        xml_tree = xml.etree.ElementTree.parse(xml_FN.getPath())
    except xml.etree.ElementTree.ParseError as e:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {0}'.format(str(e)))
        sys.exit(10)
    except IOError as e:
        log_error('(IOError) {0}'.format(str(e)))
        sys.exit(10)

    # Process DAT contents
    DAT = DATfile()
    for root_element in xml_tree.getroot():
        if root_element.tag != 'game': continue
        set = DAT.new_set()
        # Process attributes
        set['name'] = root_element.attrib['name']
        if 'cloneof' in root_element.attrib:
            set['cloneof'] = root_element.attrib['cloneof']
        # Process subtags.
        for child in root_element:
            if child.tag == 'description':
                set['description'] = child.text
            elif child.tag == 'rom':
                ROM = DAT.new_rom()
                ROM['name'] = child.attrib['name']
                ROM['size'] = int(child.attrib['size'])
                # Store hash strings as lowercase always.
                ROM['crc'] = child.attrib['crc'].upper()
                ROM['md5'] = child.attrib['md5'].upper()
                ROM['sha1'] = child.attrib['sha1'].upper()
                set['ROMs'].append(ROM)
        # Add to data object.
        DAT.sets.append(set)

    # Create indices for fast ROM data access.
    DAT.create_indices()

    # Print statistics
    log_info('DAT Sets {:,} / ROMs {:,}'.format(DAT.num_sets(), DAT.num_ROMs()))

    return DAT

# Stores all sets in a ROM collection.
class ROMcollection:
    def __init__(self, collection_conf):
        self.name = collection_conf['name'] # Collection <name>
        self.headerOffset = collection_conf['HeaderOffset'] # Collection <HeaderOffsetBytes>
        self.headerRules = collection_conf['HeaderRules']
        self.dirname = collection_conf['ROM_dir'] # <ROM_dir>
        self.num_DAT_sets = 0
        self.basename_index = {}
        self.sets = [] # List of ROMset objects. May have unknown ROM sets.
        self.file_list = [] # List of files in ROM_dir with full path name.

    # Scans files in self.dirname and fills self.file_list
    def scan_files_in_dir(self):
        ROM_dir_FN = FileName(self.dirname)
        log_info('HeaderOffset {}'.format(self.headerOffset))
        for rule in self.headerRules:
            print('HeaderRule offset {} value {}'.format(rule['offset'], rule['value']))
        log_info('Scanning files in "{}"...'.format(ROM_dir_FN.getPath()))
        if not ROM_dir_FN.exists():
            log_error('Directory does not exist "{}"'.format(ROM_dir_FN.getPath()))
            sys.exit(10)
        self.file_list = ROM_dir_FN.recursiveScanFilesInPath('*')

    # Fills self.sets and adds missing ROM sets.
    def process_files(self, DAT):
        self.num_DAT_sets = len(DAT.sets)

        # Determine status of the ROM sets (aka ZIP files).
        num_files = len(self.file_list)
        file_count = 1
        for filename in sorted(self.file_list):
            set = get_ROM_set_status(filename, DAT, self.headerOffset, self.headerRules)
            self.sets.append(set)
            sys.stdout.write("\rProcessed file {} of {}... ".format(file_count, num_files))
            sys.stdout.flush()
            file_count += 1
        sys.stdout.write("\r\n")

        # Compute indices for fast access.
        for i, rom_set in enumerate(self.sets):
            # log_debug('Index {:5d} Basename "{}"'.format(i, rom_set.basename))
            self.basename_index[rom_set.basename] = i

        # Add missing ROMs.
        # Check if sets in DAT exists, if not it add it to the list.
        # TODO Use CRC or SHA1 to add missing sets, not filenames!!!
        log_info('Adding missing ROMs...')
        num_missing = 0
        for dat_set in DAT.sets:
            # log_info('Set name "{}"'.format(dat_set['name']))
            set_zip_basename = dat_set['name'] + '.zip'
            if set_zip_basename not in self.basename_index:
                set_filename = FileName(self.dirname).pjoin(set_zip_basename).getPath()
                rom_set = ROMset(set_filename)
                rom_set.status = ROMset.SET_STATUS_MISSING
                rom = rom_set.new_rom()
                rom['name'] = dat_set['ROMs'][0]['name']
                rom['correct_name'] = dat_set['ROMs'][0]['name']
                rom['status'] = ROMset.ROM_STATUS_MISSING
                rom_set.rom_list.append(rom)
                self.sets.append(rom_set)
                num_missing += 1
        log_info('Added {} missing sets.'.format(num_missing))

        # Sort all sets alphabetically, before making index.
        # First make a list of sorted indices, then make a new sorted list with the indices.
        # https://stackoverflow.com/questions/6422700/how-to-get-indices-of-a-sorted-array-in-python
        sets_basename_list = [set.basename for set in self.sets]
        sorted_idx = [i[0] for i in sorted(enumerate(sets_basename_list), key = lambda x:x[1].lower())]
        self.sets = [self.sets[sorted_idx[i]] for i in range(len(self.sets))]

        # Refresh indices after addition of missing ROMs.
        for i, rom_set in enumerate(self.sets):
            # log_debug('Index {:5d} Basename "{}"'.format(i, rom_set.basename))
            self.basename_index[rom_set.basename] = i

# ROMset is a ZIP file that contains ROMs.
class ROMset:
    # * Set GOOD contains a single known ROM with correct name.
    # * Set BADNAME contains a single known ROM and either the ROM or the set name is wrong.
    # * Set UNKNOWN contains a single unknown ROM.
    # * MISSING sets are fake, do not exist on disk.
    # * A set can be BAD because of many different reasons:
    #   1. Set is not a ZIP file.
    #   2. The set ZIP file is corrupted or any other error.
    #   3. The set ZIP file has 2 or more files or is empty.
    # * Only BADNAME sets are fixable at the moment.
    SET_STATUS_GOOD    = 'Good   '
    SET_STATUS_BADNAME = 'BadName'
    SET_STATUS_MISSING = 'Missing'
    SET_STATUS_UNKNOWN = 'Unknown'
    SET_STATUS_ERROR   = 'Error  '

    ROM_STATUS_GOOD    = 'Good   '
    ROM_STATUS_BADNAME = 'BadName'
    ROM_STATUS_MISSING = 'Missing'
    ROM_STATUS_UNKNOWN = 'Unknown'

    def __init__(self, filename):
        self.filename = filename
        self.basename = FileName(filename).getBase()
        # Set correct name is the current one until the proper name can be determined.
        self.correct_filename = filename
        self.status = None
        self.rom_list = []

    def new_rom(self):
        return {
            'name' : '',
            'correct_name' : '',
            'size' : 0,
            'crc' : '',
            'md5' : '',
            'sha1' : '',
            'status' : ROMset.ROM_STATUS_UNKNOWN,
        }

def misc_calculate_stream_checksums(file_bytes):
    log_debug('Computing checksums of bytes stream...'.format(len(file_bytes)))
    crc_prev = 0
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    # Process bytes stream block by block
    # for piece in misc_read_bytes_in_chunks(file_bytes):
    #     crc_prev = zlib.crc32(piece, crc_prev)
    #     md5.update(piece)
    #     sha1.update(piece)
    # Process bytes in one go
    crc_prev = zlib.crc32(file_bytes, crc_prev)
    md5.update(file_bytes)
    sha1.update(file_bytes)
    crc_digest = '{:08X}'.format(crc_prev & 0xFFFFFFFF)
    md5_digest = md5.hexdigest()
    sha1_digest = sha1.hexdigest()
    size = len(file_bytes)

    checksums = {
        'crc'  : crc_digest.upper(),
        'md5'  : md5_digest.upper(),
        'sha1' : sha1_digest.upper(),
        'size' : size,
    }

    return checksums

# This function assumes sets (ZIP files) contain 1 ROM. Otherwise it is an error.
# For MAME ZIP files another function is required.
# Also, NoIntro sets with severe errors require a more sofisticated function.
def get_ROM_set_status(filename, DAT, headerOffset, headerRules):
    set = ROMset(filename)

    # Open the ZIP file.
    log_debug('\nProcessing "{}"'.format(set.basename))
    try:
        zip_f = zipfile.ZipFile(filename, 'r')
    except zipfile.BadZipfile as e:
        set.status = ROMset.SET_STATUS_ERROR
        return set

    # ZIP file must have one and only one file.
    # If set has 0 or more than 1 file that's and error.
    num_zip_files = len(zip_f.namelist())
    log_debug('zip file contains {} files'.format(num_zip_files))
    if num_zip_files != 1:
        set.status = ROMset.SET_STATUS_ERROR
        return set
    zfilename = zip_f.namelist()[0]

    # --- Build ROM list in set and calculate checksums ---
    # Decompress and calculate hashes and size.
    buffer = zip_f.read(zfilename)
    # Skip ROM header if necessary.
    if headerOffset > 0:
        rule_output = []
        for rule in headerRules:
            offset = rule['offset']
            value = rule['value']
            num_bytes = int(len(value) / 2)
            log_debug('HeaderRule offset {} num_bytes {}'.format(offset, num_bytes))
            bytes_hex = buffer[offset:offset + num_bytes].hex()
            log_debug('value     {}'.format(value))
            log_debug('bytes_hex {}'.format(bytes_hex))
            rule_output.append(value.lower() == bytes_hex.lower())
        if all(rule_output):
            log_debug('Rules verified.')
            offsetBytes = headerOffset
        else:
            log_debug('Rules NOT verified.')
            offsetBytes = 0
    else:
        offsetBytes = 0
    log_debug('offsetBytes {}'.format(offsetBytes))
    checksums = misc_calculate_stream_checksums(buffer[offsetBytes:])
    log_debug('zfilename   "{}" size {:,}'.format(zfilename, checksums['size']))
    log_debug('CRC         "{}"'.format(checksums['crc']))
    log_debug('SHA1        "{}"'.format(checksums['sha1']))
    rom = set.new_rom()
    rom['name'] = zfilename
    rom['correct_name'] = zfilename
    rom['size'] = checksums['size']
    rom['crc'] = checksums['crc']
    rom['md5'] = checksums['md5']
    rom['sha1'] = checksums['sha1']
    set.rom_list.append(rom)
    zip_f.close()

    # --- Determine status of the single ROM ---
    rom = set.rom_list[0]
    if DAT.ROM_CRC_exists(rom['crc']):
        # If ROM found check if filename is correct.
        datrom = DAT.get_ROM_CRC(rom['crc'])
        if rom['name'] == datrom['name']:
            rom['status'] = ROMset.ROM_STATUS_GOOD
            log_debug('ROM {} "{}"'.format(rom['status'], rom['name']))
        else:
            rom['status'] = ROMset.ROM_STATUS_BADNAME
            rom['correct_name'] = datrom['name']
            c_rom_name_FN = FileName(datrom['name'])
            set_FN = FileName(set.filename)
            c_set_FN = FileName(set_FN.getDir())
            c_set_FN = c_set_FN.pjoin(c_rom_name_FN.getBase_noext() + '.zip')
            set.correct_filename = c_set_FN.getPath()
            log_debug('ROM {} "{}"'.format(rom['status'], rom['name']))
            log_debug('Good Name   "{}"'.format(datrom['name']))
    else:
        # ROM not found.
        rom['status'] = ROMset.ROM_STATUS_UNKNOWN
        log_debug('ROM {} "{}"'.format(rom['status'], rom['name']))

    # --- Determine status of SET ---
    # If the ROM has a bad name mark the set as bad name.
    if rom['status'] == ROMset.ROM_STATUS_BADNAME:
        log_debug('Set status BADNAME. ROM wrong filename.')
        set.status = ROMset.SET_STATUS_BADNAME
        return set

    # If the ROM is Unknown mark the set as unknown
    elif rom['status'] == ROMset.ROM_STATUS_UNKNOWN:
        log_debug('Set status UNKNOWN. ROM unknown.')
        set.status = ROMset.SET_STATUS_UNKNOWN
        return set

    # If the ROM is good check if set has the correct name.
    # Mark it BADNAME if set name is incorrect.
    # This is a unusual case.
    elif rom['status'] == ROMset.ROM_STATUS_GOOD:
        # Determine SET correct name.
        C_ROM_FN = FileName(rom['correct_name'])
        set_FN = FileName(set.filename)
        C_set_FN = FileName(set_FN.getDir()).pjoin(C_ROM_FN.getBase_noext() + '.zip')
        log_debug('Set name    "{}"'.format(set_FN.getPath()))
        log_debug('Good name   "{}"'.format(C_set_FN.getPath()))
        set.correct_filename = C_set_FN.getPath()

        # Check if set name has the correct name.
        # The set name must be the same as the correct ROM name.
        if set_FN.getPath() != C_set_FN.getPath():
            log_debug('Set status BADNAME. ROM filename good, wrong ZIP filename.')
            set.status = ROMset.ROM_STATUS_BADNAME
            return set

    # If we reach this pint the set is good.
    set.status = ROMset.SET_STATUS_GOOD
    log_debug('Set status GOOD')

    return set

def get_collection_statistics(collection):
    stats = {
        'name' : '',
        'total' : 0,
        'have' : 0,
        'badname' : 0,
        'missing' : 0,
        'unknown' : 0,
        'error' : 0,
    }

    stats['name'] = collection.name
    stats['total_DAT'] = collection.num_DAT_sets
    for set in collection.sets:
        stats['total'] += 1
        if   set.status == ROMset.SET_STATUS_GOOD:    stats['have']    += 1
        elif set.status == ROMset.SET_STATUS_BADNAME: stats['badname'] += 1
        elif set.status == ROMset.SET_STATUS_MISSING: stats['missing'] += 1
        elif set.status == ROMset.SET_STATUS_UNKNOWN: stats['unknown'] += 1
        elif set.status == ROMset.SET_STATUS_ERROR:   stats['error']   += 1
        else:
            log_error('Unrecognised SET status. Logical error.')
            sys.exit(10)

    return stats

# Fixes a ROM set with status SET_STATUS_BADNAME
# Rename ZIP file and the single ROM in the ZIP file.
def fix_ROM_set(set):
    log_info('\nFixing set "{}"'.format(set.basename))

    # If set has not valid ROMs cannot be fixed.
    if not set.rom_list:
        log_info('Set has no ROMs, cannot be fixed.')
        return
    if set.rom_list[0]['status'] == ROMset.ROM_STATUS_UNKNOWN:
        log_info('Set has an unknown ROM, cannot be fixed.')
        return

    # First rename the set (ZIP file) and then rename the single ROM in the set.
    set_FN = FileName(set.filename)
    set_new_FN = FileName(set.correct_filename)
    if set_FN.getPath() != set_new_FN.getPath():
        log_info('MV "{}"\n-> "{}"'.format(set_FN.getPath(), set_new_FN.getPath()))
        os.rename(set_FN.getPath(), set_new_FN.getPath())
    else:
        log_info('Set name is correct "{}"'.format(set_new_FN.getPath()))
    set_fname = set_new_FN.getPath()
    set_dir = set_new_FN.getDir()
    temp_fname = os.path.join(set_dir, '_prm_.zip')
    new_rom_name = set.rom_list[0]['correct_name']

    # Then rename the compressed ROM inside the set.
    # Files in a ZIP file cannot be renamed directly.
    # Open ZIP file, read ROM in memory, overwrite ROM in ZIP file with new name.
    # https://stackoverflow.com/questions/34432130/rename-a-zipped-file-in-python
    zip_f = zipfile.ZipFile(set_fname, 'r')
    rom_name = zip_f.namelist()[0]
    zip_f.close()
    if rom_name != new_rom_name:
        log_info('Creating temp file "{}"'.format(temp_fname))
        zin = zipfile.ZipFile(set_fname, 'r')
        # zout = zipfile.ZipFile(temp_fname, 'w', compression = zipfile.ZIP_DEFLATED, compresslevel = 9)
        zout = zipfile.ZipFile(temp_fname, 'w', compression = zipfile.ZIP_DEFLATED)
        buffer = zin.read(rom_name)
        zout.writestr(new_rom_name, buffer)
        zin.close()
        zout.close()
        log_info('RM "{}"'.format(set_fname))
        os.remove(set_fname)
        log_info('MV "{}"\n-> "{}"'.format(temp_fname, set_fname))
        os.rename(temp_fname, set_fname)
    else:
        log_info('ROM name is correct "{}"'.format(rom_name))
