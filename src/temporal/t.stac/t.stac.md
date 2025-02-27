---
name: t.stac
description: Toolset for working with SpatioTemporal Asset Catalogs
---

# Toolset for working with SpatioTemporal Asset Catalogs

## DESCRIPTION

The *t.stac* toolset allows the user to explore metadata and ingest
SpatioTemporal Asset Catalog (STAC) items, collections, and catalogs.
The toolset is based on the PySTAC library and provides a set of modules
for working with STAC APIs. [STAC](https://stacspec.org/) is a
specification for organizing geospatial information in a way that is
interoperable across software and data services. The
[pystac-client](https://github.com/stac-utils/pystac-client) is used to
interact with STAC APIs.

*t.stac.catalog* *t.stac.collection* *t.stac.item* *(WIP) t.stac.export*

## REQUIREMENTS

- [pystac (>=1.12)](https://pystac.readthedocs.io/en/stable/installation.html)
- [pystac\_client (>=0.8)](https://pystac-client.readthedocs.io/en/stable/)
- [tqdm (>=4.67)](https://pypi.org/project/tqdm/)

After dependencies are fulfilled, the toolset can be installed using the
*g.extension* tool:

```sh
g.extension extension=t.stac
```

## MODULES

*[t.stac.catalog.html](t.stac.catalog.md)
[t.stac.collection.html](t.stac.collection.md)
[t.stac.item.html](t.stac.item.md)*

## AUTHOR

Corey White This work was funded by [OpenPlains
Inc.](https://openplains.com/) and the [Center for Geospatial
Analytics](https://cnr.ncsu.edu/geospatial/) at North Carolina State
University.
