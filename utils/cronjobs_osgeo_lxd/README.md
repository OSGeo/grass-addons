## What's this?

This directory contains the relevant files to generate and deploy the GRASS GIS Web pages (Hugo based, https://grass.osgeo.org/). Furthermore, source code and binary snapshots are generated as well as all manual pages and the GRASS GIS programmer's manual.

- cronjob schedule:
    - `cron_job_list_grass`
    - IMPORTANT: to activate any cronjob change, run the following on `grasslxd` container (as user `neteler`):
        - `crontab $HOME/cronjobs/cron_job_list_grass && crontab -l`
- generate and deploy the GRASS GIS Web pages at https://grass.osgeo.org/:
    - `hugo_clean_and_update_job.sh`
- GRASS GIS source code weekly snapshots:
    - grass7: `cron_grass7_main_src_snapshot.sh`
- GRASS GIS Linux binary weekly snapshots:
    - grass7: `cron_grass7_relbranch_build_binaries.sh`
- GRASS GIS addons manual pages:
    - grass7: within `cron_grass7_relbranch_build_binaries.sh`
- GRASS GIS addons overview page at https://grass.osgeo.org/grass7/manuals/addons/:
    - `compile_addons_git.sh` - called from `cron_grass7_relbranch_build_binaries.sh`
    - `grass-addons-fetch-xml.sh` - called from `cron_grass7_relbranch_build_binaries.sh`
    - `grass-addons-index.sh` - called from `cron_grass7_relbranch_build_binaries.sh`
    - `get_page_description.py` - called from `grass-addons-index.sh`
- GRASS GIS programmer's manual:
    - within `cron_grass7_relbranch_build_binaries.sh`

## Web site organisation

Important: there are two web related directories on the server:

- `/var/www/code_and_data/`: contains source code, sample data, etc.
- `/var/www/html/`: contains the hugo generated files. The relevant subdirectories of `/var/www/code_and_data/` are linked here.

## Infrastructure

The server is hosted as LXD container on `osgeo7`, see: https://wiki.osgeo.org/wiki/SAC_Service_Status#GRASS_GIS_server

The container is only accessible via the related OSGeo ssh jumphost and registered ssh pubkey.

## Cronjob execution

It is controlled via `cron_job_list_grass` on the server in:

```
grasslxd:/home/neteler/cronjobs/
```

## History

The cronjobs here have been initially written in 2002 and subsequently been updated.
