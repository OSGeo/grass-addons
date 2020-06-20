## What's this?

This directory contains the relevant files to

- generate the GRASS GIS Web pages (hugo based)
- source code weekly snapshots
- Linux binary weekly snapshots
- addon manuals
- programmer's manual

The server is hosted as LXD container on `osgeo7`, see: https://wiki.osgeo.org/wiki/SAC_Service_Status#GRASS_GIS_server
It is only accessible via ssh jumphost.

## Cronjob execution

It is controlled via `cron_job_list_grass` on the server in:

```
grasslxd:/home/neteler/cronjobs/
```

## History

The cronjobs here have been initially written in 2002 and subsequently updated.
