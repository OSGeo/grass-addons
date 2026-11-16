## DESCRIPTION

The *i.sentinel3.import* module allows importing
[Copernicus Sentinel-3 products](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-3).

The Sentinel-3 product types are provided in different formats. Not all
of them are currently directly supported by GDAL. Some, like the SLSTR
products, consist of several netCDF4 files, where geometry and image
information are stored in different files. Therefore, a GRASS specific
import routine has been implemented for those formats. This routine
imports the data pixel-wise after transforming the coordinates from
WGS84 into the projection of the current project.
*[r.in.xyz](https://grass.osgeo.org/grass-stable/manuals/r.in.xyz.html)*
is then used to read the values into a raster map. Thus, *the user has
to set the computational region extent to import the data of interest*.
The resolution is set from the resolution of the input bands and pixels
are aligned to the pixel grid of the current region.

Currently, only import of the following **product\_type**s is
implemented:

- S3SL1RBT: SL\_1\_RBT\_\_ products from Sentinel-3 SLSTR
- S3SL2LST: SL\_2\_LST\_\_ products from Sentinel-3 SLSTR

All Sentinel-3 scene files provided in the **input** option are
mosaicked into one resulting granule with one map for each imported
band. The **input** option accepts either one or many path(s) to
Sentinel-3 archives (.zip) separated by comma or a text file with one
Sentinel-3 archive per row. The module is designed to produce temporally
non-overlapping mosaics along the tracks of the satellite. Input should
therefore not mix data from different tracks, sensing periods, or
missions (Sentinel-3A / Sentinel-3B). The module gives a warning if data
from different tracks is used as input.

Users can provide a custom **basename**, to which band names are
appended. Otherwise, the basename is constructed from the input scenes
following the Sentinel-3 file naming convention. Here, the frame id is
stripped from the resulting basename, the start of sensing time is set
to the start of sensing time of the first input scene and the end of
sensing time is set to the end of the last input scene.

Ancillary data and quality flag data can be imported as well using the
**anxillary\_bands** and **flag\_bands** options. Here, the user has to
specify the product specific band names or *all* to import all
available bands of the given kind. Quality flags are imported as
categorical maps with the flag meanings as category labels.

For each imported band both scene and band specific metadata are written
into the map history
(*[r.support](https://grass.osgeo.org/grass-stable/manuals/r.support.html)*).
Also, sensing time is written into the timestamp of the map. After
import, the metadata can be retrieved with *r.info -e*.

*i.sentinel3.import* imports the selected bands with the resolution and
extent of the current region (except for the solar bands), unless the
**-n** flag is used to import bands with their native resolution
(usually 500m or 1000m).

Pixels flagged as invalid in the product are not imported. Missing
pixels are interpolated with
*[r.fill.stats](https://grass.osgeo.org/grass-stable/manuals/r.fill.stats.html)*,
which smooths the data unless the **-k** flag is used to keep the
original values.

With the **-r** flag, radiance bands are rescaled to reflectance (this
requires the solar angle bands, which are imported as well). The
**maximum\_solar\_angle** option limits the import to pixels with a
solar zenith angle lower than the given value. Both are only available
for product type S3SL1RBT.

With the **-c** flag, the land surface temperature (*LST*) is imported
in degree celsius instead of kelvin. The *LST\_uncertainty* is a
temperature difference and is always imported in kelvin.

## NOTES

*i.sentinel3.import* does ONLY support projected coordinate systems and
assumes map units to be meter.

By means of the **register\_output** option *i.sentinel3.import* allows
creating a file which can be used to register imported imagery data into
a space-time raster dataset (STRDS) with
*[t.register](https://grass.osgeo.org/grass-stable/manuals/t.register.html)*.
See examples below.

### Metadata storage

By using the **-j** flag the band metadata are additionally stored in
JSON format (in the current mapset under `cell_misc`).

## EXAMPLES

### Import Sentinel-3 data

Import all Sentinel-3B RBT data of a given start date and track found in
the `data` directory, store metadata as JSON files within the GRASS
database directory, keep pixel values during interpolation (no
smoothing), import bands at native resolution and rescale radiance bands
to reflectance:

```sh
i.sentinel3.import -k -n -r -j \
    input="$(find data/ -iname "S3B*RBT*____20240129*_089_094_*.zip" | tr '\n' ',' | sed 's/,$/\n/')" \
    product_type=S3SL1RBT register_output=data/reg.txt nprocs=8 --v --o

# register imported data into existing STRDS
t.register input=Sentinel_3 file=data/reg.txt
```

### Register imported Sentinel-3 data into STRDS

```sh
i.sentinel3.import -k -n -c -j \
    input="$(find data/ -iname "S3B*LST*____20240129*_089_094_*.zip" | tr '\n' ',' | sed 's/,$/\n/')" \
    product_type=S3SL2LST register_output=data/reg.txt nprocs=8 --v --o

# register imported data into existing STRDS
t.register input=Sentinel_3_LST file=data/reg.txt
```

A register file contains the following columns, separated by `|`:
imported raster map name, start and end timestamp as well as the
semantic label, see the example below:

```text
S3B_SL_2_LST_20240129205026_20240129205326_089_094_ESA_O_NT_004_LST@PERMANENT|2024-01-29 20:50:26|2024-01-29 20:53:26|S3_LST
S3B_SL_2_LST_20240129205026_20240129205326_089_094_ESA_O_NT_004_LST_uncertainty@PERMANENT|2024-01-29 20:50:26|2024-01-29 20:53:26|S3_LST_uncertainty
```

## REQUIREMENTS

The following Python libraries are required:

- GDAL (install through system software management)
- numpy
- netcdf4
- python-dateutil
- cf-units (for unit conversion)

## SEE ALSO

*[Overview of i.sentinel toolset](i.sentinel.md)*

*[i.sentinel.download](i.sentinel.download.md),
[r.fill.stats](https://grass.osgeo.org/grass-stable/manuals/r.fill.stats.html),
[r.in.xyz](https://grass.osgeo.org/grass-stable/manuals/r.in.xyz.html),
[t.register](https://grass.osgeo.org/grass-stable/manuals/t.register.html)*

## AUTHORS

Stefan Blumentrath, Norway
