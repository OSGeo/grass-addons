## DESCRIPTION

*i.landsat.download* allows to search and download Landsat TM, ETM and
OLI data from [USGS EarthExplorer](https://earthexplorer.usgs.gov/) and
[Planetary Computer](https://planetarycomputer.microsoft.com/) using
[EODAG](https://eodag.readthedocs.io/en/stable/) Python library.

Landsat data are organized in tiers: Newly-acquired Landsat scenes are
placed in the Real-Time (RT) tier. After reprocessing they are
transitioned to either Tier 1 (T1; scenes with the highest available
data quality, considered suitable for time-series analysis) or Tier 2
(T2; less accurate geometry). The Tier designation (T1, T2, RT) is
indicated at the end of the Landsat Product Identifier.

The supported Landsat satellites include (see also [Landsat satellite
chronology](https://en.wikipedia.org/wiki/Landsat_program#Satellite_chronology)):

- Landsat 5 (TM): 1984 to 2013
- Landsat 7 (ETM+): 1999 to present (note: [Landsat 7 ETM+ SLC-off
    error](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-7)
    after May 31, 2003)
- Landsat 8 (OLI): 2013 to present
- Landsat 9 (OLI-2): 2021 to present

The dataset names and IDs are:

| Dataset Name                        | Dataset ID           |
| ----------------------------------- | -------------------- |
| Landsat 5 TM Collection 2 Level 1   | `landsat_tm_c2_l1`   |
| Landsat 5 TM Collection 2 Level 2   | `landsat_tm_c2_l2`   |
| Landsat 7 ETM+ Collection 2 Level 1 | `landsat_etm_c2_l1`  |
| Landsat 7 ETM+ Collection 2 Level 2 | `landsat_etm_c2_l2`  |
| Landsat 8 Collection 2 Level 1      | `landsat_8_ot_c2_l1` |
| Landsat 8 Collection 2 Level 2      | `landsat_8_ot_c2_l2` |
| Landsat 9 Collection 2 Level 1      | `landsat_9_ot_c2_l1` |
| Landsat 9 Collection 2 Level 2      | `landsat_9_ot_c2_l2` |

By default, only products which footprint intersects current computation
region extent (area of interest, AOI) are filtered. The AOI can be
optionally defined by a vector **map**. In this case, the vector will be
used as AOI.

To only list available scenes, **l** flag must be set. If no **start**
or **end** dates are provided, the module will search scenes from the
past 60 days.

To download all scenes found within the time frame provided, the user
must remove the **l** flag and provide an **output** directory.
Otherwise, files will be downloaded into */tmp* directory. To download
only selected scenes, one or more IDs must be provided through the
**id** option, along with an **output** directory. In addition, a
**timeout** (in seconds) can be set to define how long a request should
wait for a response before aborting (default is 300 seconds).

## NOTES

### Settings

*i.landsat.download* reads the user credentials either from the terminal
or from the **settings** file. This file must contain two lines in case
of USGS provider, or one line in case of Planetary Computer provider.

User credentials can be also defined interactively when **settings=-**
is given. Note that interactive prompt does not work in the graphical
user interface.

Alternatively, if the settings option is not specified
*i.landsat.download* will attempt to use credentials stored in the
default EODAG configuration file in `$HOME/.config/eodag/eodag.yml`.
Note any parameter set in the configuration file, e.g. 'extract' to
specify whether to extract the downloaded scenes or not, will be used by
*i.landsat.download*, unless overriden by user options. **Exception:**
output parameter in EODAG configuration file is not used by
*i.landsat.download*, and the default output directory is the current
working directory.

### USGS EarthExplorer

To connect to EarthExplorer both a *username* and a *password* are
required. See the [register](https://ers.cr.usgs.gov/register) page for
signing up.

USGS settings file:

```text
myusername
mypassword
```

USGS interactive settings:

```text
Insert username: myusername
Insert password:
```

### Planetary Computer

Most datasets are anonymously accessible, but a subscription key may be
needed to [increase rate limits and access private
datasets.](https://planetarycomputer.microsoft.com/docs/concepts/sas/#rate-limits-and-access-restrictions)
Users can
[create an account](https://planetarycomputer.microsoft.com/account/request), and
then view their keys by signing in with their [Microsoft account](https://planetarycomputer.developer.azure-api.net/).

Planetary computer settings file:

```sh
apikey
```

Planetary computer interactive settings:

```sh
Insert API key:
```

Note: to use Plantery Computer anonymously the settings option should
not be used.

## EXAMPLES

Search available scenes:

```sh
i.landsat.download -l settings=credentials.txt \
    dataset=landsat_8_ot_c2_l2 clouds=15 \
    datasource=usgs start='2018-08-24' end='2018-12-21'
```

Download all available scenes:

```sh
i.landsat.download settings=credentials.txt \
    dataset=landsat_8_ot_c2_l2 clouds=15 \
    datasource=usgs start='2018-08-24' end='2018-12-21' \
    timeout=600
```

Download selected scenes by ID anonymously from Planetary Computer:

```sh
i.landsat.download datasource=planetary_computer \
    id=LC09_L2SP_015035_20240529_02_T1,LC09_L2SP_015035_20240614_02_T1 \
    output=/tmp
```

## REQUIREMENTS

- [EODAG
    library](https://eodag.readthedocs.io/en/stable/getting_started_guide/install.html)
    (install with `pip install eodag`)

## SEE ALSO

*[Overview of i.landsat tools](i.landsat.md)*

*[i.landsat.import](i.landsat.import.md),
[i.landsat.qa](i.landsat.qa.md),
[i.landsat.toar](https://grass.osgeo.org/grass-stable/manuals/i.landsat.toar.html)*

*[Landsat Collection 1
info](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-collection-1?qt-science_support_page_related_con=1#qt-science_support_page_related_con)*

*[Landsat Collection 2
info](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-collection-2?qt-science_support_page_related_con=2#qt-science_support_page_related_con)*

## AUTHOR

[Veronica Andreo](https://veroandreo.gitlab.io/), CONICET, Argentina.
