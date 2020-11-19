## What's this?

This directory contains the relevant files to

- cronjob schedule:
    - `cron_job_list_grass`
- generate and deploy the GRASS GIS Web pages (hugo based, https://staging.grass.osgeo.org/):
    - `hugo_clean_axnd_update_job.sh`
- GRASS GIS source code weekly snapshots:
    - release_branch_7_8: `cron_grass78_src_relbr78_snapshot.sh`
    - master: `cron_grass7_HEAD_src_snapshot.sh`
- GRASS GIS Linux binary weekly snapshots:
    - `cron_grass78_releasebranch_78_build_bins.sh`
- GRASS GIS addons manual pages:
    - within `cron_grass78_releasebranch_78_build_bins.sh`
- GRASS GIS addons overview page at https://grass.osgeo.org/grass7/manuals/addons/:
    - `compile_addons_git.sh`
    - `get_page_description.py`
    - `grass-addons-fetch-xml.sh`
    - `grass-addons-index.sh`
- GRASS GIS programmer's manual:
    - within `cron_grass7_HEAD_build_bins.sh`

The server is hosted as LXD container on `osgeo7`, see: https://wiki.osgeo.org/wiki/SAC_Service_Status#GRASS_GIS_server

The container is only accessible via the ssh jumphost.

## Cronjob execution

It is controlled via `cron_job_list_grass` on the server in:

```
grasslxd:/home/neteler/cronjobs/
```

## History

The cronjobs here have been initially written in 2002 and subsequently updated.
