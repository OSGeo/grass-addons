## DESCRIPTION

*i.modis.import* imports Level-3 MODIS (Moderate Resolution Imaging
Spectroradiometer, flown on the two NASA spacecrafts Terra and Aqua)
products into GRASS GIS.

## NOTES

The *i.modis* modules need the [pyModis](https://www.pymodis.org)
library. Please install it beforehand.

The input file is given as a list of full paths to the MODIS HDF files,
one per line. The input file(s) have to be inside the folder where the
HDF files are stored.

**If *mrtpath* is not used, pyModis will use GDAL to convert HDF files
to TIF (which is faster).**

The *mrtpath* option is the path to the main folder of the MODIS
Reprojection Tools (MRT) binaries, i.e. the folder which contains the
bin/ and the data/ folder, since these two folders are essential for
obtaining a successful result.

**Warning**:

  - When using the MODIS Reprojection Tools to convert HDF files, only
    the following projection systems are supported: Lambert Azimuthal
    Equal Area, Lambert Conformal Conic, Mercator, Polar Stereographic,
    Transverse Mercator, Universal Transverse Mercator.
  - Using GDAL allows to handle all projections supported by Proj4.

NOTE: In order to work with the temporal framework of GRASS GIS the flag
*w* must be set during the import with *i.modis.import*.

### Default subset of layers to import

User-defined subset of layers can be specified by **spectral** option.
If not given, default values are applied.

#### MODIS AOD - Aerosol Optical Depth

|                                                                              |          |             |
| ---------------------------------------------------------------------------- | -------- | ----------- |
| SDS layer                                                                    | Spectral | Spectral QA |
| Aerosol Optical Depth at 047 micron                                          | 0        | 0           |
| Aerosol Optical Depth at 055 micron                                          | 1        | 1           |
| AOD Uncertainty at 047 micron                                                | 0        | 0           |
| Fine-Mode Fraction for Ocean                                                 | 0        | 0           |
| Column Water Vapor in cm liquid water                                        | 0        | 0           |
| AOD QA                                                                       | 0        | 1           |
| AOD Model (Regional background model used)                                   | 0        | 0           |
| Injection Height (Smoke injection height over local surface height) Grid 5km | 0        | 0           |
| Cosine of Solar Zenith Angle                                                 | 0        | 0           |
| Cosine of View Zenith Angle                                                  | 0        | 0           |
| Relative Azimuth Angle                                                       | 0        | 0           |
| Scattering Angle                                                             | 0        | 0           |
| Glint Angle                                                                  | 0        | 0           |

## EXAMPLES

### General examples

Import of a single file with all the subsets (QA layers included) using
GDAL:

```sh
i.modis.import input=/path/to/file
```

Import of files from a list with all the subsets using MRT (if mrtpath
is not provided, GDAL is used):

```sh
i.modis.import files=/path/to/listfile mrtpath=/path/to/mrt
```

Import of files from a list as mosaics per date without QA layers using
MRT:

```sh
i.modis.import -mq files=/path/to/listfile mrtpath=/path/to/mrt
```

Import of a single file with user-specific subset of layers using GDAL:

```sh
i.modis.import input=/path/to/file spectral="( 1 0 1 0 )"
```

Import of files from a list with user-specific subset of layers and
without QA layer using MRT:

```sh
i.modis.import -q files=/path/to/listfile mrtpath=/path/to/mrt spectral="( 1 )"
```

Import of a single subset of layers (i.e.: spectral="( 1 )") from each
file of a list and write an *outfile* to be used with *t.register* to
assign timestamps to maps in the temporal database and register them in
a spacetime dataset. This option uses GDAL:

```sh
i.modis.import -wq files=/path/to/listfile spectral="( 1 )" outfile=/path/to/list_for_tregister.csv
```

### Import of global MODIS NDVI data

The MOD13C1 is a global NDVI/EVI 16 days map product which can be
downloaded and imported as follows in a latitude-longitude GRASS GIS
location:

```sh
# download the two years worth of data
i.modis.download settings=~/.rmodis product=ndvi_terra_sixteen_5600 \
  startday=2015-01-01 endday=2016-12-31 folder=$USER/data/ndvi_MOD13C1.061
# import band 1 = NDVI
i.modis.import files=$USER/data/ndvi_MOD13C1.061/listfileMOD13C1.061.txt spectral="( 1 )" \
  method=bilinear outfile=$USER/data/ndvi_MOD13C1.061/list_for_tregister.csv -w
# create empty temporal DB
t.create type=strds temporaltype=absolute output=ndvi_16_5600m title="Global NDVI 16 days MOD13C1" \
  description="MOD13C1 Global NDVI 16 days" semantictype=mean
# register maps within spacetime datasets (the file name is provided by
# i.modis.import using -w flag and outfile option)
t.register input=ndvi_16_5600m file=$USER/data/ndvi_MOD13C1.061/list_for_tregister.csv

# verify and visualize timeline
t.rast.list ndvi_16_5600m
g.gui.timeline ndvi_16_5600m
```

### Example of a complete workflow

Download the data: MOD11A1 from 2016-12-23 to 2016-12-31, tiles
h18v04,h18v05

```sh
i.modis.download settings=$HOME/SETTING product=lst_terra_eight_1000 \
 tiles=h18v04,h18v05 startday=2016-12-23 endday=2016-12-31
```

Import mosaics of LST Day and QC Day bands for all dates in the list of
files:

```sh
i.modis.import -m files=$HOME/listfileMOD11A1.061.txt \
 spectral="( 1 1 0 0 0 0 0 0 0 0 0 0 )"
```

Extract and apply the mandatory QA band (for more details see
[i.modis.qc](https://grass.osgeo.org/grass-stable/manuals/i.modis.qc.html)):

```sh
for map in `g.list type=raster pattern="*_QC_Day"` ; do
 i.modis.qc input=${map} output=${map}_mandatory_qa \
  productname=mod11A1 qcname=mandatory_qa_11A1
done

for m in `g.list rast pat=*2016*LST_Day_1km` ; do
 # get name of product and date from filenames
 i=`echo $m | cut -c 1-16`
 # apply qa flags
 r.mapcalc --o expression="${m} = if(${i}_mosaic_QC_Day_mandatory_qa < 2, ${m}, null())"
done
```

Create the time series (i.e.: spacetime dataset) and register maps in
it:

```sh
t.create type=strds temporaltype=absolute output=LST_Day_daily \
 title="Daily LST Day 1km" \
 description="Daily LST Day 1km MOD11A1.061, December 2016"
t.register -i input=LST_Day_daily \
 maps=`g.list type=raster pattern="*2016*LST_Day_1km" separator=comma` \
 start="2016-12-23" increment="1 day"
```

Verify list of maps and dates and visualize timeline:

```sh
t.rast.list LST_Day_daily
g.gui.timeline LST_Day_daily
```

It is also possible to create a time series using the list of maps with
start and end time written by *i.modis.import* with the *w* flag and
outfile option.

```sh
# Import mosaics of LST Day for all dates using the list of downloaded files from
# i.modis.download (see above) and get a list of the imported files along with
# dates to use with t.register in the temporal framework
i.modis.import -mw files=$HOME/listfileMOD11A1.061.txt \
 spectral="( 1 0 0 0 0 0 0 0 0 0 0 0 )" outfile=$HOME/list_for_tregister.csv

# Create time series and register maps
t.create type=strds temporaltype=absolute output=LST_Day_daily \
 title="Daily LST Day 1km" \
 description="Daily LST Day 1km MOD11A1.061, December 2016"
t.register input=LST_Day_daily file=$HOME/list_for_tregister.csv
```

## SEE ALSO

*[i.modis](i.modis.md), [i.modis.download](i.modis.download.md),
[i.modis.qc](https://grass.osgeo.org/grass-stable/manuals/i.modis.qc.html)*

[GRASS GIS Wiki: temporal data
processing](https://grasswiki.osgeo.org/wiki/Temporal_data_processing)

[Map of MODIS Land products' Sinusoidal grid tiling
system](https://lpdaac.usgs.gov/dataset_discovery/modis)

## AUTHOR

Luca Delucchi, Google Summer of Code 2011; subsequently updated.
