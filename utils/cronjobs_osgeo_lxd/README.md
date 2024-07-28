# Cronjobs OSGeo LXD

## Version overview

| **label**      | **meaning**                                                     |
| -------------- | --------------------------------------------------------------- |
| legacy         | legacy stable version, no longer recommended                    |
| old            | old stable version, still in use                                |
| current stable | current stable version (recommended)                            |
| preview        | development version, for developers and new feature enthusiasts |

The name of the cronjob files reflects the GRASS GIS version being compiled/packaged.
The actual version numbers are only coded in the scripts themselves.

## What's this?

This directory contains the relevant files to generate and deploy the GRASS GIS
Web pages (Hugo based, <https://grass.osgeo.org/>). Furthermore, source code and
binary snapshots are generated as well as all manual pages and the GRASS GIS
programmer's manual.

- cronjob schedule:
  - `cron_job_list_grass`
  - IMPORTANT: to activate any cronjob change, run the following on `grasslxd`
    container (as user `neteler`):
    - `crontab $HOME/cronjobs/cron_job_list_grass && crontab -l`
- generate and deploy the GRASS GIS Web pages at <https://grass.osgeo.org/>:
  - `hugo_clean_and_update_job.sh`
- GRASS GIS source code weekly snapshots:
  - `cron_grass_legacy_src_snapshot.sh`
  - `cron_grass_old_src_snapshot.sh`
  - `cron_grass_current_stable_src_snapshot.sh`
  - `cron_grass_preview_src_snapshot.sh`
- GRASS GIS Linux binary weekly snapshots:
  - `cron_grass_legacy_build_binaries.sh`
  - `cron_grass_old_build_binaries.sh`
  - `cron_grass_current_stable_build_binaries.sh`
  - `cron_grass_preview_build_binaries.sh`
- GRASS GIS addons manual pages:
  - addon manual pages are generated within above Linux binary weekly snapshots
- GRASS GIS 7 addons overview page at <https://grass.osgeo.org/grass7/manuals/addons/>:
  - `compile_addons_git.sh` - called from `cron_grass_legacy_build_binaries.sh`
  - `build-xml.py` - called from `cron_grass_legacy_build_binaries.sh`,
    generates the modules.xml file required for the g.extension module
  - `grass-addons-index.sh` - called from `cron_grass_legacy_build_binaries.sh`
  - `get_page_description.py` - called from `grass-addons-index.sh`
- GRASS GIS 8 addons overview page at <https://grass.osgeo.org/grass8/manuals/addons/>:
  - `compile_addons_git.sh` - called from `cron_grass_XXX_build_binaries.sh`
  - `build-xml.py` - called from `cron_grass_XXX_build_binaries.sh`
    generates the modules.xml file required for the g.extension module
  - `grass-addons-index.sh` - called from `cron_grass_XXX_build_binaries.sh`
  - `get_page_description.py` - called from `grass-addons-index.sh`
- GRASS GIS programmer's manual:
  - within `cron_grass_XXX_build_binaries.sh`
- compilation addons:
  - `compile_addons_git.sh` it's called with `$5` arg, addon is
    installed into own individual directory, with **bin/ docs/ etc/ scripts/**
    subdir e.g. db.join addon dir `$HOME/.grass8/addons/db.join/`, instead of
    directory structure`$HOME/.grass8/addons/` where **bin/ docs/ etc/ scripts/**
    subdir are shared across all installed addons (this dir structure is used
    to install the addon using the `g.extension` module). Addon installed directory
    is set via global variable [`GRASS_ADDON_BASE`](https://github.com/OSGeo/grass-addons/pull/656/commits/8c08184415ec32fe409bf09b2599b0506d7650ab#diff-f0fc8363c0e166fdbe9eecb74a9e261498ec0bbf15500e56b1bb1b5ba7afb900L119),
    e.g. for db.join addon is`GRASS_ADDON_BASE=$HOME/.grass8/addons/db.join/`.
    Before compilation and installation is downloaded [addons_paths.json](https://github.com/OSGeo/grass-addons/pull/656/commits/8c08184415ec32fe409bf09b2599b0506d7650ab#diff-f0fc8363c0e166fdbe9eecb74a9e261498ec0bbf15500e56b1bb1b5ba7afb900R128)
    but only once, for first compiled addon, and then this file is moved to
    [one level directory up](https://github.com/OSGeo/grass-addons/pull/656/commits/8c08184415ec32fe409bf09b2599b0506d7650ab#diff-f0fc8363c0e166fdbe9eecb74a9e261498ec0bbf15500e56b1bb1b5ba7afb900R133)
    to sharing for all next compiled add-ons, to prevent download this file
    again in next addon compilation loop e.g. move
    `$HOME/.grass8/addons/db.join/addons_paths.json` -> `$HOME/.grass8/addons/addons_paths.json`.
    Next during addon compilation addon is called
    [mkhtml.py](https://github.com/OSGeo/grass/blob/main/utils/mkhtml.py)
    script (generate html manual page), `get_addon_path()` function, where is
    the parsed global variable `GRASS_ADDON_BASE` (base directory of installed
    addon), where is trying to find the **addons_paths.json** file and in
    [directory one level up](https://github.com/OSGeo/grass/pull/2054/commits/5a374101a825c451675d18b0d59e6ac99ee6cb02#diff-3e1684c5c5d40b273b6488a9b5a5558f556d2bcf2973ba5106b6125e01aa6959R314).
    When the add-on was found among the official add-ons, the source code
    and add-on history URL are set on the html man page, the entire man
    page is generated.

## Web site organisation

Important: there are two web related directories on the server:

- `/var/www/code_and_data/`: contains source code, sample data, etc.
- `/var/www/html/`: contains the hugo generated files. The relevant
  subdirectories of `/var/www/code_and_data/` are linked here.

## Infrastructure

The server is hosted as LXD container on `osgeo7`, see:
<https://wiki.osgeo.org/wiki/SAC_Service_Status#grass>

The container is only accessible via the related OSGeo ssh jumphost and
registered ssh pubkey.

## Cronjob execution

It is controlled via `cron_job_list_grass` on the server in:

```text
grasslxd:/home/neteler/cronjobs/
```

## History

The cronjobs here have been initially written in 2002 and subsequently been updated.
