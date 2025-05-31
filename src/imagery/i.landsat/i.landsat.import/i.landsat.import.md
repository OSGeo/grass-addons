## DESCRIPTION

The *i.landsat.import* module allows importing Landsat 5, 7 and 8
products downloaded by the *[i.landsat.download](i.landsat.download.md)*
module.

By default *i.landsat.import* imports all Landsat bands within the scene
files found in the **input** directory. The number of scene files can be
optionally reduced with the **pattern\_file** option. In this option, a
regular expression for filtering the file names can be given, e.g.
'229083' for importing only scenes from path 229 and row 083.

By default *i.landsat.import* imports the full scene. Optionally, the
import can be reduced to the computational region extent with
**extent=region**.

Note that in case that the spatial reference system of the input data
differs from that of the GRASS GIS target location, the input data will
be reprojected internally by means of
*[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html)*.
To speed up this process, a higher than default value can be specified
for the **memory** option.

If the user wants to ignore an insignificant mismatch in the spatial
reference system, the projection check can be suppressed with the **-o**
flag and data will be imported directly.

Alternatively, input data can be linked by means of
*[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html)*
using **-l** flag. Note that linking data requires that Landsat input
data and GRASS location have the same spatial reference system (e.g.,
the same UTM zone). Take into account that USGS provides all Landsat
products in UTM north zones whether they belong to North or South
Hemisphere.

The number of Landsat bands to be imported can be optionally reduced by
the **pattern** option. Below an overview of Landsat 5 TM, 7 ETM and 8
OLI band's spatial resolution:

| Spatial resolution \[m\] | L5 Bands               | L7 Bands               | L8 Bands                       |
| ------------------------ | ---------------------- | ---------------------- | ------------------------------ |
| 15                       | \--                    | B8                     | B8                             |
| 30                       | B1, B2, B3, B4, B5, B7 | B1, B2, B3, B4, B5, B7 | B1, B2, B3, B4, B5, B6, B7, B9 |
| 60                       | \--                    | B6                     | \--                            |
| 100                      | \--                    | \--                    | B10, B11                       |
| 120                      | B6                     | \--                    | \--                            |

Note that while the original resolution of band 6 in Landsat 5 TM and
Landsat 7 ETM is 120 and 60 m respectively, they are provided with a
resampled resolution of 30 m. For further details about bands wavelength
and scene size, visit the [band
designations](https://www.usgs.gov/faqs/what-are-band-designations-landsat-satellites?qt-news_science_products=0#qt-news_science_products)
page at USGS website.

The file naming convention for Landsat scenes is explained in detail on
the [USGS Landsat Collections Level-1 Scene Naming Convention FAQ](https://www.usgs.gov/faqs/what-naming-convention-landsat-collections-level-1-scenes).

With the **register\_output** option *i.landsat.import* allows to create
a text file that can be used to register imported imagery data into a
space-time raster dateset (STRDS) by means of
*[t.register](https://grass.osgeo.org/grass-stable/manuals/t.register.html)*.
A register file typically contains 2 or 3 columns with the map name and
start time or the map name plus start and end time in the case of
interval time type. Landsat data is considered to be of *instance* time
type, i.e., we only have one point in time. Hence, the output register
file will contain the map name and start time separated by `|` when
using GRASS GIS stable version. In the case of GRASS GIS development
version which supports the band reference concept (see
*[i.band.library](https://grass.osgeo.org/grass-devel/manuals/i.band.library.html)*
module for details), the output register file is extended by a third
column containing the band reference information, see the examples
below.

## EXAMPLES

### List Landsat bands to import

At first, print the list of raster files to be imported by **-p**. For
each file also projection match with current location is printed
including detected input data EPSG code:

```sh
i.landsat.import -p input=data
```

### Import Landsat data

Limit import to only 4th and 5th bands:

```sh
i.landsat.import input=data pattern='B(4|5)'
```

Limit import to all bands with 30m resolution:

```sh
i.landsat.import input=data pattern='B(1|2|3|4|5|6|7|9)'
```

Link Landsat data:

```sh
i.landsat.import -l input=data
```

Link data from specific path and row while ignoring projection check

```sh
i.landsat.import -l -o input=data pattern_file='229083'
```

Limit import to bands 4 and 5 for path 229 and row 083 in 2019

```sh
i.landsat.import input=data pattern_file='229083_2019' pattern='B(4|5)'
```

Limit import to optical, NIR, thermal and QA\_PIXEL using a regular
expression (Landsat-8):

```sh
i.landsat.import input=data pattern='(B(2|3|4|5|6|7|8|10|11)|QA_PIXEL)'
```

Limit import to bands 4 and 5 for path 229 and row 083 in 2019 and get a
txt file to use in *t.register*

```sh
i.landsat.import input=data pattern_file='229083_2019' pattern='B(4|5)' \
    register_output=t_register.txt

# create a STRDS and register imported data
t.create output=landsat_ts title="Landsat 8 time series" \
    description="Landsat 8 data, path-row 229-83, year 2020"
t.register input=landsat_ts file=t_register.txt
```

## SEE ALSO

*[Overview of i.landsat tools](i.landsat.md)*

*[i.landsat.download](i.landsat.download.md),
[i.landsat.qa](i.landsat.qa.md),
[i.landsat.toar](https://grass.osgeo.org/grass-stable/manuals/i.landsat.toar.html),
[i.landsat8.swlst](https://grass.osgeo.org/grass-stable/manuals/addons/i.landsat8.swlst.html),
[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html),
[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html)*

## AUTHOR

[Veronica Andreo](https://veroandreo.gitlab.io/), CONICET, Argentina.
