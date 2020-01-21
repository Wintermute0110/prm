# Python ROM Manager command reference

## Invocation

```
prm COMMAND [SETNAME] [OPTIONS]
```

## Configuration file

The configuration file must be named `configuration.xml`. Next is an example of
`configuration.xml`:

```
<!-- Example configuration file for prm -->
<general>
    <DATdirectory>/home/kodi/DATs/</DATdirectory>
    <Incoming_directory>/home/kodi/incoming/</Incoming_directory>
</general>

<set>
    <name>snes</name>
    <DAT>automatic</DAT>
    <platform>snes</platform>
    <ROMdir>/home/kodi/ROMs/nintendo-snes/</ROMdir>
</set>

<set>
    <name>megadrive</name>
    <DAT>automatic</DAT>
    <platform>megadrive</platform>
    <ROMdir>/home/kodi/ROMs/sega-megadrive/</ROMdir>
</set>

<set>
    <name>mame</name>
    <DAT>automatic</DAT>
    <platform>mame</platform>
    <ROMdir>/home/kodi/ROMs/ROMs-mame/</ROMdir>
</set>

<set>
    <name>mame2003plus</name>
    <DAT>automatic</DAT>
    <platform>mame</platform>
    <ROMdir>/home/kodi/ROMs/ROMs-mame2003plus/</ROMdir>
    <Sourcedir>/home/kodi/ROMs/ROMs-mame/</Sourcedir>
    <Sourcedir>/home/kodi/ROMs/ROMs-mame-roolback/</Sourcedir>
</set>
```

## Command list

### `listsets`

Display all the ROM sets in the configuration file.

Command example:
```
$ prm listsets
```

### `listplatforms`

Display a list of prm platform names. Platform names are used to automatically pick a
DAT file.

### `scan SETNAME`

Scans the ROMs 

Command example:
```
$ prm scan megadrive
```

### `status SETNAME`

Shows the status of a previously scanned ROM set.

Command example:
```
$ prm status megadrive
```

### `fix SETNAME`

Fixes in place a ROM set. Currently only renames ZIP files and ROMs.

After a fix it is a good idea to rescan your set to check everything is all right.

Command example:
```
$ prm fix megadrive
```

### `rebuild SETNAME`

**Planned feature**

Rebuilds a ROM set taking ROMs from one or more `<Sourcedir>` and copying to the correct
place with the correct name to `<ROMdir>`. ROMs in `<Sourcedir>` are never modified.

Example:
```
$ prm rebuild mame2003plus
```

### `sort`

**Planned feature**

Scans the ROMs in the `<Incoming_directory>`, identifies them and tries to place them
in the correct ROM set directories.
