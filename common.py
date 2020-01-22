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
import fnmatch
import os
import pprint
import re
import sys
import xml.etree.ElementTree
import zipfile

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
def pprint(level, print_str):
    # --- Write to console depending on verbosity
    if level <= log_level:
        print(print_str)

    # --- Write to file
    if file_log_flag and level <= log_level:
        if print_str[-1] != '\n': print_str += '\n'
        f_log.write(print_str) # python will convert \n to os.linesep

# --- Some useful function overloads
def log_error(print_str):
    pprint(LOG_ERROR, print_str)

def log_warn(print_str):
    pprint(LOG_WARN, print_str)

def log_info(print_str):
    pprint(LOG_INFO, print_str)

def log_verb(print_str):
    pprint(LOG_VERB, print_str)

def log_debug(print_str):
    pprint(LOG_DEBUG, print_str)

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
        'MAME_DAT_dir',
        'Incoming_dir',
    ]
    collection_tag_set = [
        'name',
        'platform',
        'DAT',
        'ROM_dir',
    ]

    def __init__(self):
        # Dictionary of strings. Key is the XML tag name in <common>.
        # Uses OrderedDict() to keep order as found in the config file.
        self.common_opts = self.new_common_dic()
        # Dictionary of dictionaries. Key is the collection name.
        # Uses OrderedDict() to keep order as found in the config file.
        self.collections = OrderedDict()

    def new_common_dic(self):
        return OrderedDict([
            ('NoIntro_DAT_dir', ''),
            ('MAME_DAT_dir', ''),
            ('Incoming_dir', ''),
        ])

    def new_collection_dic(self):
        return OrderedDict([
            ('name', ''),
            ('platform', ''),
            ('DAT', ''),
            ('ROM_dir', ''),
        ])

# Parses configuration file using ElementTree.
# Returns a ConfigFile object
parse_rjust = 16
def parse_File_Config(options):
    log_info('\033[1mParsing configuration file\033[0m')
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
# DTD "http://www.logiqx.com/Dats/datafile.dtd"
def audit_new_rom_logiqx(): 
    rom = {
        'name'         : '',
        'cloneof'      : '',
        'year'         : '',
        'manufacturer' : ''
    }

    return rom

# Loads a No-Intro XML DAT file. Returns a data structure like:
# dat = {
#     'rom_name_A' : {
#         'name' : 'rom_name_A',
#         'cloneof' : '',
#         'rom_name_parent
#     },
# }
def load_XML_DAT_file(xml_FN):
    if not xml_FN.exists():
        log_error('Does not exists "{0}"'.format(xml_FN.getPath()))
        sys.exit(10)

    # Parse using ElementTree
    dat = {}
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
    for root_element in xml_tree.getroot():
        if root_element.tag == 'game':
            nointro_rom = audit_new_rom_logiqx()
            rom_name = root_element.attrib['name']
            nointro_rom['name'] = rom_name
            if 'cloneof' in root_element.attrib:
                nointro_rom['cloneof'] = root_element.attrib['cloneof']
            dat[rom_name] = nointro_rom

    return dat

# ROMset is a ZIP file that contains ROMs.
class ROMset:
    # Status not yet computed.
    SET_STATUS_UNKNOWN = 'Unknown'
    # Set contains a single known ROM with correct name.
    SET_STATUS_GOOD    = 'Good   '
    # Set contains a single known ROM with incorrect name.
    SET_STATUS_BADNAME = 'BadName'
    # Set is not a ZIP file or the ZIP file is corrupted or any other error.
    SET_STATUS_BAD     = 'Bad    '

    def __init__(self):
        self.filename = ''
        self.status = ROMset.SET_STATUS_UNKNOWN
        self.rom_list = []

    def new_rom(self):
        return {
            'name' : '',
            'crc' : '',
            'md5' : '',
            'sha1' : '',
            'status' : '',
        }

def get_ROM_set_status(filename):
    set = ROMset()
    set.filename = filename
    set.status = ROMset.SET_STATUS_UNKNOWN

    # Open the ZIP file.
    log_debug('Processing "{}"'.format(filename))
    try:
        zip_f = zipfile.ZipFile(filename, 'r')
    except zipfile.BadZipfile as e:
        set.status = ROMset.SET_STATUS_BAD
        return set

    # ZIP file must have one and only one file.
    zip_file_list = []
    for zfile in zip_f.namelist():
        z_info = zip_f.getinfo(zfile)
        size = z_info.file_size
        CRC = '{0:08x}'.format(z_info.CRC)
        log_debug('zfile "{}"'.format(zfile))
        log_debug('Size {:,} CRC {}'.format(size, CRC))
        zip_file_list.append({
            'fname' : zfile,
            'size' : size,
            'CRC' : CRC,
        })
    zip_f.close()

    # If set has 0 or more than 1 file that's and error.
    if len(zip_file_list) != 1:
        set.status = ROMset.SET_STATUS_BAD
        return set

    # Determine status of the ROM file.
    # Look for the ROM in the DAT file by searching the CRC.
    # Should we trust the CRC in the ZIP file or should we decompress the data and calculate
    # our own checksums?
    

    return set

# Fixes a ROM set with status SET_STATUS_BADNAME
# Rename ZIP file and the single ROM in the ZIP file.
def fix_ROM_set(set):
    pass
