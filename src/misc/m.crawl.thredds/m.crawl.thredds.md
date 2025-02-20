## DESCRIPTION

An increasing amount of spatio-temporal data, like climate observations
and forecast data or satellite imagery is provided through [Thredds Data
Servers (TDS)](https://www.unidata.ucar.edu/software/tds/).

*m.crawl.thredds* crawls the catalog of a Thredds Data Server (TDS)
starting from the catalog-URL provided in the **input**. It is a wrapper
module around the Python library
[thredds\_crawler](https://github.com/ioos/thredds_crawler).
*m.crawl.thredds* returns a list of dataset URLs, optionally with
additional information on the service type and data size. Depending on
the format of the crawled datasets, the output of *m.crawl.thredds* may
be used as input to *t.rast.import.netcdf*.

The returned list of datasets can be filtered:

  - based on the modification time of the dataset using a range of
    relevant timestamps defined by the **modified\_before** and
    **modified\_after** option(s)
  - based on the file name using a regular expression in the **filter**
    option.

When crawling larger Thredds installations, skipping irrelevant branches
of the server's tree of datasets can greatly speed-up the process. In
the **skip** option, branches (and also leaf datasets) can be excluded
from the search by a comma-separated list of regular expression strings,
e.g. ".\*metadata.\*" would direct the module to not look for datasets
inside a "metadata" directory.

Authentication to the Thredds Server (if required) can be provided
either through a text-file, where the first line contains the username
and the second the password, or by interactive user input (if
*authentication=-*). Alternatively, username and password can be passed
through environment variables *THREDDS\_USER* and *THREDDS\_PASSWORD*.

## NOTES

The Thredds data catalog is crawled recursively. Providing the URL to
the root of a catalog on a Thredds server with many hierarchies and
datasets can therefore be quite time consuming, even if executed in
parallel (**nprocs** \> 1).

## EXAMPLES

List modelled climate observation datasets from the Norwegian
Meteorological Institute (met.no)

```sh
# Get a list of all data for "seNorge"
m.crawl.thredds input="https://thredds.met.no/thredds/catalog/senorge/seNorge_2018/Archive/catalog.xml"
https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2021.nc
(...)
https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_1957.nc

# Get a list of the most recent data for "seNorge"
m.crawl.thredds input="https://thredds.met.no/thredds/catalog/senorge/seNorge_2018/Archive/catalog.xml" modified_after="2021-02-01"
https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2021.nc
https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2020.nc

# Get a list of the most recent data for "seNorge" that match a regular expression
# Note the "." beofor the "*"
m.crawl.thredds input="https://thredds.met.no/thredds/catalog/senorge/seNorge_2018/Archive/catalog.xml" \
modified_after="2021-02-01" filter=".*2018_202.*"
https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2021.nc
https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2020.nc
```

List Sentinel-2A data from the Norwegian Ground Segment (NBS) for the 2.
Feb 2021

```sh
# Get a list of all Sentinel-2A data for 2. Feb 2021 with dataset size
m.crawl.thredds input="https://nbstds.met.no/thredds/catalog/NBS/S2A/2021/02/28/catalog.xml" print="data_size"
https://nbstds.met.no/thredds/fileServer/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T35WPU_20210228T201033_DTERRENGDATA.nc|107.6
(...)
https://nbstds.met.no/thredds/fileServer/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T32VNL_20210228T201033_DTERRENGDATA.nc|166.1

# Get a list of WMS end-points to all Sentinel-2A data for 2. Feb 2021
m.crawl.thredds input="https://nbstds.met.no/thredds/catalog/NBS/S2A/2021/02/28/catalog.xml" services="wms"
https://nbstds.met.no/thredds/wms/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T35WPU_20210228T201033_DTERRENGDATA.nc
(...)
https://nbstds.met.no/thredds/wms/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T32VNL_20210228T201033_DTERRENGDATA.nc
```

## REQUIREMENTS

*m.crawl.thredds* is a wrapper around the
[thredds\_crawler](https://github.com/ioos/thredds_crawler) Python
library.

## SEE ALSO

*[i.sentinel.download](https://grass.osgeo.org/grass-stable/manuals/addons/i.sentinel.download.html),
[t.rast.import.netcdf](https://grass.osgeo.org/grass-stable/manuals/addons/t.rast.import.netcdf.html)*

## AUTHORS

Stefan Blumentrath, [Norwegian Institute for Nature Research (NINA),
Oslo](https://www.nina.no/Kontakt/Ansatte/Ansattinformasjon.aspx?AnsattID=14230)
