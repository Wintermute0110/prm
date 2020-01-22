# Python ROM Manager command reference

`prm` is the ROM manager for No-Intro ROM collections.

No-Intro ROM sets have one ROM. In other words, each set ZIP file has one and only one ROM file.
On the other hand, MAME ROM sets may have one or more than one ROM. Because every No-Intro ROM
set have a single ROM, `prm` only reports ROMs and not ROM sets. In `prm`, set and ROM
can be used interchangeably.

Note that both `prm` and `prm-mame` share the same configuration file named `configuration.xml`.

## Invocation

```
prm COMMAND [COLLECTION] [OPTIONS]
```

## Configuration file

The configuration file must be named `configuration.xml`. This is an example of
`configuration.xml`:

```
<!-- Example configuration file for prm. -->
<common>
    <NoIntro_DAT_directory>/home/kodi/DATs-NoIntro-standard/</NoIntro_DAT_directory>
    <MAME_DAT_directory>/home/kodi/DATs-mame/</MAME_DAT_directory>
    <Incoming_directory>/home/kodi/incoming/</Incoming_directory>
</common>

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

Display all the ROM collections in the configuration file.

The DAT file can be specified in the `<DAT>` tag, for example `<DAT>/home/kodi/DATs/megadrive.dat</DAT>`.
If the automatic option is used `<DAT>automatic</DAT>`, then `prm` will pick a DAT file
automatically from the directory `<NoIntro_DAT_directory>` in the `<common>` section.

Command example:
```
$ prm listcollections
Set name      Platform   DAT file
--------------------------------
snes          snes       Nintendo - Super Nintendo Entertainment System (Combined) (20191027-010632).dat
megadrive     megadrive  Sega - Mega Drive - Genesis (20191120-213041).dat
```

### `listplatforms`

Display a list of prm platform names. Platform names are used to automatically pick a
DAT file.

Command example:
```
Long name        Short name            Compact name  Alias
--------------------------------------------------------------
MAME             arcade-mame           mame          None 
Nintendo SNES    nintendo-snes         snes          None
Sega Genesis     sega-genesis          genesis       megadrive
Sega Mega Drive  sega-megadrive        megadrive     None
```

### `scan COLLECTION`

Scans the ROMs in a collection. ROM ZIP files are in the directory `<ROMdir>` defined
on each `<collection>`. After the scanner completes, the results are stored
for later display.

A ROMs has `BadName` if the ROM has a wrong name or the ZIP file has a wrong name or both.

`Unknown ROMs` means a ZIP file with unknown contents or a non-ZIP file.

Command example:
```
$ prm scan megadrive
Scanning ROM collection megadrive
...
Set STATUS "/home/kodi/ROMs/sega-megadrive/Sonic.zip"
ROM STATUS "Sonic.md" 
...
=== Scanner results ===
Collection    megadrive
Total ROMs    1,234
Have ROMs     1,234
Miss ROMs     1,234
Unknown ROMs  1,234
BadName ROMs  1,234
```

### `scanall`

Scans all the collections.

### `status COLLECTION`

Shows the status of a previously scanned ROM set.

Command example:
```
$ prm status megadrive
Collection    megadrive
Total ROMs    1,234
Have ROMs     1,234
Miss ROMs     1,234
Unknown ROMs  1,234
BadName ROMs  1,234
```

### `statusall`

Shows the status of all the previously scanned ROM collections.

Command example:
```
$ prm status megadrive
Collection    Platform   Total ROMs  Have ROMs  Miss ROMs  Unknown ROMs  BadName ROMs
-------------------------------------------------------------------------------------
snes          snes            1,234      1,234      1,124         1,123         1,123
megadrive     megadrive       1,234      1,234      1,124         1,123         1,123
```

### `fix COLLECTION`

Fixes in place a ROM set. Currently only renames ZIP files and ROMs inside ZIP files.

After a fix command completes it is a good idea to rescan your set to check
everything is all right.

Command example:
```
$ prm fix megadrive
```

### `fixall`

Fixes all the collections.

### `sort`

**Planned feature**

Scans the ROMs in the `<Incoming_directory>` defined in the `<general>` section, identifies
them and tries to place them in the correct ROM collection directories.
