## DESCRIPTION

The *i.sentinel.download* addon allows downloading Sentinel satellite
products from the [Copernicus Data Space
Ecosystem](https://dataspace.copernicus.eu/).

### Copernicus Data Space Ecosystem

Using the Copernicus Data Space Ecosystem for searching and downloading
Copernicus Sentinel data is the default option. The following product
types (parameter **producttype**) are currently supported for download
from the **Copernicus Data Space Ecosystem**:

- Sentinel-1 (SAR; available from Oct 2014 to present day) (SAR)
    [products](https://sentinel.esa.int/web/sentinel/missions/sentinel-1/data-products):
  - SLC: Single Look Complex (Level-1)
  - GRD: Ground Range Detected (Level-1)
  - GRDCOG: COG format based Ground Range Detected (Level-1)
  - OCN: Ocean products for wind, wave and currents applications
        (Level-2)
- Sentinel-2 (optical and infrared; available from July 2015 to
    present day) (optical)
    [products](https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products):
  - S2MSI2A: operational Bottom-Of-Atmosphere reflectances in
        cartographic geometry Level-2A)
  - S2MSI1C: Top-Of-Atmosphere reflectances in cartographic geometry
        (Level-1C)
- Sentinel-3 (OLCI and SLSTR instrument data products at level 2, for
    OLCI sensor also Level 1; available from April 2018 to present day)
    (optical)
    [products](https://sentinel.esa.int/web/sentinel/missions/sentinel-3/data-products):
  - S3OL1EFR: Land colour and atmosphere TOA radiances at full
        resolution
  - S3OL1ERR: Land colour and atmosphere TOA radiances at reduced
        resolution
  - S3SL1RBT: Brightness temperatures and radiances
  - S3OL2WFR: Ocean colour, water and atmosphere geophysical
        parameters
  - S3OL2WRR: Ocean colour, water and atmosphere geophysical
        parameters at reduced resolution
  - S3OL2LFR: Land colour and atmosphere geophysical parameters
  - S3OL2LRR: Land colour and atmosphere geophysical parameters at
        reduced resolution
  - S3SL2LST: Land Surface Temperature
  - S3SL2FRP: Fire Radiative Power
  - S3SR2LAN: Land Surface Height
  - S3SY2SYN: Surface Reflectance and Aerosol parameters over Land
  - S3SY2VGP: 1 km VEGETATION-Like product (\~VGT-P) - TOA
        Reflectance
  - S3SY2VG1: 1 km VEGETATION-Like product (\~VGT-S1) 1 day
        synthesis surface reflectance and NDVI
  - S3SY2V10: 1 km VEGETATION-Like product (\~VGT-S10) 10 day
        synthesis surface reflectance and NDVI
  - S3SY2AOD: Global Aerosol parameter over land and sea on super
        pixel resolution (4.5 km x 4.5 km)

To connect to the Copernicus Data Space Ecosystem both a *user* name and
*password* are required; see [Register new
account](https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/auth?client_id=cdse-public&redirect_uri=https%3A%2F%2Fdataspace.copernicus.eu%2Fbrowser%2F&response_type=code&scope=openid)
page for signing up.

### Copernicus Open Access Hub (DEPRECTAED)

[Copernicus Open Access Hub](https://scihub.copernicus.eu/) is now
permanently closed. To continue accessing Copernicus Sentinel data,
Copernicus Data Space Ecosystem is now the new successor.

### USGS Earth Explorer (DEPRECATED)

### Google Cloud Storage (DEPRECATED)

### Credentials file

*i.sentinel.download* reads the user credentials from the **settings**
file. The file must contain at least two lines:

```text
myusername
mypassword
```

## NOTES

The data hub to download from can be indicated with the **datasource**
option. ESA's Copernicus Data Space Ecosystem is the default, and
currently only, option.

User credentials can be also defined interactively when **settings=-**
is given. Note that interactive prompt does not work in the graphical
user interface.

```text
Insert username: myusername
Insert password:
```

By default Sentinel products are sorted by *cloudcoverpercentage* and
*ingestiondate* (see **sort** option). By default, only products which
footprint intersects current computation region extent (area of
interest, AOI) are filtered. The AOI can be optionally defined also by
vector **map**. In addition the spatial relation between AOI and the
footprint (**area\_relation**) can be set to

- *Contains*: to only return scenes where the AOI is contained inside
    the footprint (Only supported by Copernicus Data Space Ecosystem)
- *IsWithin*: to only return scenes where the footprint is contained
    inside the AOI (Only supported by Copernicus Data Space Ecosystem)
- *Intersects*: to return all scenes where the footprint intersects
    the AOI (default)

Filtered products can be reduced by **limit** option.

*i.sentinel.download* limits the default search for products to the last
60 days; an exact date range can be defined by **start** and **end**
parameters to search beyond that.

Sentinel products can be also filtered by **producttype** or, in case of
S2MSI1C, S2MSI2A, S3SY2SYN, S3SY2VGP, S3SY2VG1, S3SY2VG1 and S3SY2AOD,
maximum **clouds** cover percentage.

Extra search keywords can be specified with **query**. Multiple keywords
can be listed separated with comma (e.g.
'polarizationChannels=VV\&VH,orbitdirection=ASCENDING').

**List of Some Queryables:**

- orbitNumber
- timeliness (e.g. NT, NRT-3h, etc...)
- processingBaseline
- polarizationChannels (e.g. VV\&VH)
- storageStatus

Note refer to i.eodag to get a list of all queryables. Note that text
based queryables have to be upper-case. Scenes with unavailbe queryable
information are filtered out (e.g. if a product has the timeliness
queryable set as **Null**, then it will be filtered out if you use
query="timeliness=NT"). If a scene doesn't have a queryable as part of
its metadata, the scene will be silently maintained without any
warnings.

*i.sentinel.download* also allows downloading of Sentinel products by
specifying a (list of) ID, where ID refers to the scene name on
Copernicus Data Space Ecosystem. This operation is performed by the
**id** option. Note that this option is mutually exclusive with all
other filtering options. The **id** option also accepts text files with
(list of) ID, one ID per line.

In case a Sentinel data download was interrupted, *i.sentinel.download*
will restart the download for the paritally downloaded data, from
scratch, once the command is re-excuted.

The **output** directory is created if not yet available. Default is
current working directory.

## EXAMPLES

### List filtered products

Find all atmospherically corrected Sentinel-2 L2A products (S2MSI2) in
2018 (area in Italy as an example):

```sh
g.region n=42 w=12 s=41 e=13 res=0:01 -p

i.sentinel.download -l settings=credentials.txt producttype=S2MSI2A start=2018-01-01 end=2018-12-31

1062 Sentinel product(s) found.
S2B_MSIL2A_20180124T101309_N9999_R022_T32TQL_20230726T165433 2018-01-24T10:13:09   0% S2MSI2A 43.38 MB
S2B_MSIL2A_20180124T101309_N9999_R022_T33TTF_20230726T182752 2018-01-24T10:13:09   0% S2MSI2A 42.07 MB
S2A_MSIL2A_20180129T101251_N9999_R022_T32TQM_20221022T182543 2018-01-29T10:12:51   0% S2MSI2A 613.37 MB
S2A_MSIL2A_20180129T101251_N9999_R022_T33TTG_20221023T032353 2018-01-29T10:12:51   0% S2MSI2A 630.21 MB
S2B_MSIL2A_20180210T100139_N9999_R122_T32TQM_20221022T182154 2018-02-10T10:01:39   0% S2MSI2A 0.98 GB
S2B_MSIL2A_20180210T100139_N9999_R122_T33TTG_20221023T032353 2018-02-10T10:01:39   0% S2MSI2A 996.95 MB
[...]
```

Sort products by **ingestiondate**, limit cloud coverage to 3% per
scene:

```sh
g.region n=42 w=12 s=41 e=13 res=0:01 -p
i.sentinel.download -l settings=credentials.txt producttype=S2MSI2A start=2018-01-01 end=2018-12-31 sort=ingestiondate order=desc clouds=3

197 Sentinel product(s) found.
S2B_MSIL2A_20180928T100019_N0208_R122_T32TQM_20180928T180353 2018-09-28T10:00:19   0% S2MSI2A 0.0 MB
S2B_MSIL2A_20180928T100019_N0208_R122_T33TUF_20180928T180353 2018-09-28T10:00:19   1% S2MSI2A 0.0 MB
S2B_MSIL2A_20180928T100019_N0208_R122_T33TUG_20180928T180353 2018-09-28T10:00:19   1% S2MSI2A 0.0 MB
S2B_MSIL2A_20180928T100019_N0208_R122_T32TQL_20180928T180353 2018-09-28T10:00:19   0% S2MSI2A 234.59 MB
S2B_MSIL2A_20180928T100019_N0208_R122_T33TTG_20180928T180353 2018-09-28T10:00:19   0% S2MSI2A 0.0 MB
[...]
```

Create a vector map of **footprints** of S-2 scenes with **clouds**
limited to 3% per scene (note that topological errors will be shown
since some footprint overlap):

```sh
g.region n=42 w=12 s=41 e=13 res=0:01 -p
i.sentinel.download -l settings=credentials.txt producttype=S2MSI2A start=2018-01-01 end=2018-12-31 clouds=1 footprints=s2_scenes_footprints

Writing footprints into <s2_scenes_footprints<...
197 scene(s) found.
[...]
S2B_MSIL2A_20180210T100139_N9999_R122_T32TQM_20221022T182154 2018-02-10T10:01:39   0% S2MSI2A 0.98 GB
S2B_MSIL2A_20180210T100139_N9999_R122_T33TTG_20221023T032353 2018-02-10T10:01:39   0% S2MSI2A 996.95 MB
S2A_MSIL2A_20180406T100031_N0206_R122_T33TUF_20180406T120928 2018-04-06T10:00:31   0% S2MSI2A 0.0 MB
S2A_MSIL2A_20181023T100051_N9999_R122_T32TQM_20221022T181952 2018-10-23T10:00:51   0% S2MSI2A 1.0 GB
S2A_MSIL2A_20181023T100051_N9999_R122_T33TTG_20221023T032324 2018-10-23T10:00:51   0% S2MSI2A 0.99 GB
S2A_MSIL2A_20181205T101401_N9999_R022_T32TQM_20221022T180259 2018-12-05T10:14:01   0% S2MSI2A 625.52 MB
[...]
```

Find Sentinel-2 L1C products (S2MSI1C) of **last 60 days** (default)
covering current computation region extent:

```sh
g.region n=42 w=12 s=41 e=13 res=0:01 -p
i.sentinel.download -l settings=credentials.txt producttype=S2MSI1C sort=ingestiondate

100 scene(s) found.
S2B_MSIL1C_20240611T100559_N0510_R022_T33TTF_20240611T120915 2024-06-11T10:05:59  40% S2MSI1C 327.18 MB
S2B_MSIL1C_20240611T100559_N0510_R022_T32TQL_20240611T120915 2024-06-11T10:05:59  40% S2MSI1C 359.88 MB
S2B_MSIL1C_20240611T100559_N0510_R022_T33TTG_20240611T120915 2024-06-11T10:05:59  49% S2MSI1C 522.2 MB
S2B_MSIL1C_20240611T100559_N0510_R022_T32TQM_20240611T120915 2024-06-11T10:05:59  48% S2MSI1C 503.76 MB
S2A_MSIL1C_20240613T100031_N0510_R122_T32TQM_20240613T134114 2024-06-13T10:00:31  33% S2MSI1C 759.46 MB
[...]
```

Find Sentinel-1 products by one or several specified **ID**s:

```sh
i.sentinel.download -l settings=credentials.txt id=S1A_IW_SLC__1SDV_20240609T052012_20240609T052039_054242_0698FA_72DA --quiet
S1A_IW_SLC__1SDV_20240609T052012_20240609T052039_054242_0698FA_72DA 2024-06-09T05:20:12   0% S2MSI2A 7.71 GB
```

Find Sentinel-1 products within a specified date range and filter by a
particular polarisation mode using the **query** parameter (refer to
the [Copernicus SciHub User Guide](https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch)
for details on available query options):

```sh
i.sentinel.download -l settings=credentials.txt producttype=SLC start=2018-01-01 end=2018-12-31 query='polarizationChannels=VV&VH'
393 scene(s) found.
S1B_IW_SLC__1SDV_20180101T051051_20180101T051118_008973_010039_B427 2018-01-01T05:10:51 cloudcover_NA SLC 7.47 GB
S1B_IW_SLC__1SDV_20180101T051116_20180101T051143_008973_010039_CF15 2018-01-01T05:11:16 cloudcover_NA SLC 7.46 GB
S1A_IW_SLC__1SDV_20180101T170507_20180101T170535_019964_021FFD_BC68 2018-01-01T17:05:07 cloudcover_NA SLC 7.7 GB
S1A_IW_SLC__1SDV_20180101T170532_20180101T170559_019964_021FFD_E2C9 2018-01-01T17:05:32 cloudcover_NA SLC 7.41 GB
S1B_IW_SLC__1SDV_20180102T165631_20180102T165658_008995_0100F0_5814 2018-01-02T16:56:31 cloudcover_NA SLC 7.71 GB
S1B_IW_SLC__1SDV_20180106T051902_20180106T051929_009046_0102AB_009C 2018-01-06T05:19:02 cloudcover_NA SLC 7.47 GB
[...]
```

Find Sentinel-2 L1C products (S2MSI1C) covering an exemplary region in
Germany with temporal and cloud filter.

```sh
g.region n=51 w=6 s=50 e=7 res=0:01 -p

i.sentinel.download start=2017-09-01 end=2017-12-01 clouds=10 producttype=S2MSI1C settings=credentials.txt -l
40 scene(s) found.
S2B_MSIL1C_20171015T104009_N0205_R008_T32ULB_20171015T104525 2017-10-15T10:40:09   0% S2MSI1C 0.0 MB
S2B_MSIL1C_20171015T104009_N0500_R008_T31UGS_20231026T234139 2017-10-15T10:40:09   0% S2MSI1C 807.9 MB
S2B_MSIL1C_20171015T104009_N0500_R008_T32ULB_20231026T234139 2017-10-15T10:40:09   0% S2MSI1C 807.19 MB
S2A_MSIL1C_20171017T103021_N0205_R108_T31UGR_20171017T103024 2017-10-17T10:30:21   0% S2MSI1C 0.0 MB
S2A_MSIL1C_20171017T103021_N0500_R108_T31UGR_20231015T102148 2017-10-17T10:30:21   0% S2MSI1C 460.84 MB
[...]
```

### Download Sentinel products

Download first (**limit=1**) S2MSI2A product found into the *data*
directory:

```sh
g.region n=42 w=12 s=41 e=13 res=0:01 -p
i.sentinel.download settings=credentials.txt producttype=S2MSI2A start=2018-05-01 end=2018-05-31 limit=1 output=s2_L2A_may2018/
```

The downloaded Sentinel data can subsequently be easily imported into
GRASS GIS using *[i.sentinel.import](i.sentinel.import.md)* module.

### Download Sentinel products by ID

Example of downloading a single Sentinel product by ID:

```sh
i.sentinel.download settings=credentials.txt id=S2B_MSIL2A_20180210T100139_N9999_R122_T32TQM_20221022T182154 output=s2_data/
```

## REQUIREMENTS

- [i.eodag](i.eodag.md)
- [EODAG
    library](https://eodag.readthedocs.io/en/stable/getting_started_guide/install.html)
    (install with `pip install eodag`)

## SEE ALSO

*[Overview of i.sentinel toolset](i.sentinel.md)*

*[i.sentinel.import](i.sentinel.import.md),
[i.sentinel.preproc](i.sentinel.preproc.md),
[i.sentinel.mask](i.sentinel.mask.md),
[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html),
[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html),
[v.import](https://grass.osgeo.org/grass-stable/manuals/v.import.html)*

Finding UUID by Sentinel scene name (example:
'S2B\_MSIL2A\_20190724T103029\_N0213\_R108\_T32ULA\_20190724T130550'):  

1. Visit the following page:
    [browser.dataspace.copernicus.eu](https://browser.dataspace.copernicus.eu/)  
2. Go into the "Search" tab.
3. Paste Sentinel scene ID into the Search Box, and press Search.
4. A single scene should show up. Press the info icon on the bottom
    right of the scene.
5. The UUID is shown in the URL at the bottom of the scene window,
    between brackets.  
    (e.g.
    <https://zipper.dataspace.copernicus.eu/odata/v1/Products(**3cfcc58f-8316-5df0-b55e-e1831e745b51**)/$value>)
    so the UUID is **3cfcc58f-8316-5df0-b55e-e1831e745b51** in this case

See also [GRASS GIS Workshop in
Jena](https://training.gismentors.eu/grass-gis-workshop-jena/units/20.html)
for usage examples.

## AUTHORS

Martin Landa, [GeoForAll
Lab](https://geomatics.fsv.cvut.cz/research/geoforall/), CTU in Prague,
Czech Republic with support of
[OpenGeoLabs](https://opengeolabs.cz/en/home/) company  
Guido Riembauer, [mundialis](https://www.mundialis.de/) (USGS and GCS
provider support)  
[Hamed Elgizery](https://github.com/HamedElgizery), Giza, Egypt. (EODAG
Migration)
