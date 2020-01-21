# Python ROM Manager command reference

## Invocation

```
prm COMMAND [COLLECTION] [OPTIONS]
```

## Configuration file

The configuration file must be named `configuration.xml`. Next is an example of
`configuration.xml`:

```
<!-- Example configuration file for prm. -->
<general>
    <NoIntro_DAT_directory>/home/kodi/DATs-NoIntro-standard/</NoIntro_DAT_directory>
    <MAME_DAT_directory>/home/kodi/DATs-mame/</MAME_DAT_directory>
    <Incoming_directory>/home/kodi/incoming/</Incoming_directory>
</general>

<collection>
    <name>snes</name>
    <DAT>automatic</DAT>
    <platform>snes</platform>
    <ROMdir>/home/kodi/ROMs/nintendo-snes/</ROMdir>
</collection>

<collection>
    <name>megadrive</name>
    <DAT>automatic</DAT>
    <platform>megadrive</platform>
    <ROMdir>/home/kodi/ROMs/sega-megadrive/</ROMdir>
</collection>

<collection>
    <name>mame</name>
    <DAT>/home/kodi/DATs-mame/mame-0217.dat</DAT>
    <platform>mame</platform>
    <ROMdir>/home/kodi/ROMs/ROMs-mame/</ROMdir>
</collection>

<collection>
    <name>mame2003plus</name>
    <DAT>automatic</DAT>
    <platform>mame</platform>
    <ROMdir>/home/kodi/ROMs/ROMs-mame2003plus/</ROMdir>
    <Sourcedir>/home/kodi/ROMs/ROMs-mame/</Sourcedir>
    <Sourcedir>/home/kodi/ROMs/ROMs-mame-roolback/</Sourcedir>
</collection>
```

## Command list

### `listcollections`

Display all the ROM sets in the configuration file.

Command example:
```
$ prm listsets
Set name      Platform   DAT file
--------------------------------
snes          snes       zxcvzxcv.dat
megadrive     megadrive  zxcvzxcv.dat
mame          mame       zxcvzxcv.dat
mame2003plus  mame       zxcvzxcv.dat
```

### `listplatforms`

Display a list of prm platform names. Platform names are used to automatically pick a
DAT file.

Command example:
```
Long name                               Short name            Compact name  Alias
-------------------------------------------------------------------------------------
MAME                                    arcade-mame           mame          None 
Nintendo SNES                           nintendo-snes         snes          None
Sega Genesis                            sega-genesis          genesis       megadrive
Sega Mega Drive                         sega-megadrive        megadrive     None
```

### `scan COLLECTION`

Scans the ROMs in a collection. ROM ZIP files are in the directory `<ROMdir>`.

Command example:
```
$ prm scan megadrive
Scanning ROM collection megadrive
...
Scanner results (missing/total)
Sets ROMs

```

### `status COLLECTION`

Shows the status of a previously scanned ROM set.

Command example:
```
$ prm status megadrive
```

### `statusall`

Shows the status of all the previously scanned ROM collections.

Command example:
```
$ prm status megadrive
Collection    Platform   Total sets Have sets  Miss sets Unknown sets Total ROMs Have ROMs Miss ROMs Unknown ROMs
-----------------------------------------------------------------------------------------------------------------
snes          snes       3,128
megadrive     megadrive  
mame          mame       
```

### `fix COLLECTION`

Fixes in place a ROM set. Currently only renames ZIP files and ROMs.

After a fix it is a good idea to rescan your set to check everything is all right.

Command example:
```
$ prm fix megadrive
```

### `rebuild COLLECTION`

**Planned feature**

Rebuilds a ROM set taking ROMs from one or more `<Sourcedir>` and copying to the correct
place with the correct name to `<ROMdir>`. ROMs in `<Sourcedir>` are never modified.

Example:
```
$ prm rebuild mame2003plus
```

### `sort`

**Planned feature**

Scans the ROMs in the `<Incoming_directory>` defined in the `<general>` section, identifies
them and tries to place them in the correct ROM collection directories.
