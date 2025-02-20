## DESCRIPTION

*t.rast.import.netcdf* imports content of one or more NetCDF files into
a GRASS GIS Space Time Raster Dataset (STRDS). NetCDF files are expected
to follow the [CF-convention](https://cfconventions.org/). Files not
adhering to those standards may fail to import.

Input URL(s) to NetCDF files can be provided in the **input** option as
either a file, with one URL to a dataset per line, a comma-separated
list of URLs or a single URL. "-" causes input to be taken from stdin.

The module works for both local and remote data (e.g. on a Thredds
Server). Data can be imported via *r.in.gdal* or linked with
*r.external*.

*t.rast.import.netcdf* uses GDALs Virtual Raster format (VRT) if data's
Coordinate Reference system differs from the one of the current location
where they are supposed to be imported.

Reprojection on import is done using GDAL warp if necessary. In that
case, users should be aware of the extent and resolution of the data to
import and the current computational region. Import is limited to and
aligned with the current computational region, if the **r-flag** is set.
Otherwise, extent and resolution in the target CRS is guessed by GDAL.
Import of global data to coordinate systems that do not support that
extent will thus fail.

Starting with GRASS GIS version 8.0, different variables or subdatasets
in a NetCDF file can be imported as "semantic\_label" into one STRDS. To
achieve this, a configuration file has to be provided in the
**semantic\_labels** option. That configuration file maps subdatasets in
the NetCDF file to GRASS GIS semantic\_labels. Each line in that file
must have the following format: ` 
input_netcdf_subdataset=grass_gis_semantic_label ` The equal sign *=* is
required. If a semantic\_labels configuration file is provided, the
import of subdatasets is limited to those subdatasets listed in the
file. Hence, it can be used to filter variables of interest.

## KNOWN ISSUES

The VRT format is also used when linking NetCDF data that contains
subdatasets, as subdatasets are currently not supported in *r.external*.

Reading NetCDF files directly via HTTP protocol (like in the examples
below) is currently not supported on MS Windows.

GDAL versions prior to 3.4.1 do not support reading NetCDF files
directly via HTTP protocol on newer Linux kernels either. Please make
sure to have at least GDAL version 3.4.1 on recent Linux systems. See
posts on the [GDAL-dev mailing
list](https://www.mail-archive.com/gdal-dev@lists.osgeo.org/msg37419.html).
for reference.

## REQUIREMENTS

Support of semantic\_labels is only available with GRASS GIS 8.0 or
later. *t.rast.import.netcdf* uses the following non-standard Python
modules:

  - [numpy](https://pypi.org/project/numpy)
  - [GDAL](https://pypi.org/project/GDAL) (preferably version \>= 3.4.1)
  - [cf-units](https://pypi.org/project/cf-units)

## EXAMPLES

### Link Sentinel-2 scenes from the Norwegian Ground Segment

```sh
# Choose Scenes to import (see also m.crawl.thredds module)
echo "https://nbstds.met.no/thredds/fileServer/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T35WPU_20210228T201033_DTERRENGDATA.nc
https://nbstds.met.no/thredds/fileServer/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T32VNL_20210228T201033_DTERRENGDATA.nc" > nc.txt

# Create a semantic_label configuration file
echo "B1=S2_1
B2=S2_2" > semantic_labels.conf

# Import data (link NetCDF files without downloading them)
t.rast.import.netcdf -l input=nc.txt output=S2A semantic_labels=semantic_labels.conf \
memory=2048 nprocs=2 nodata="-1"
```

### Import Norwegian Climate data

```sh
# Create a semantic_label configuration file
echo "tg=temperature_avg
tn=temperature_min" > semantic_labels.conf

# Import data within a selected time window
t.rast.import.netcdf output=SeNorge semantic_labels=semantic_labels.conf \
memory=2048 nprocs=2 start_time="2020-08-01" end_time="2021-08-01" \
input=https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2020.nc
```

### Append to STRDS from previous imports

```sh
# Choose dataset to import (see also m.crawl.thredds module)

# Create a semantic_label configuration file
echo "tg=temperature_avg
tn=temperature_min" > semantic_labels.conf

# Import data within a selected time window
t.rast.import.netcdf output=SeNorge semantic_labels=semantic_labels.conf \
memory=2048 nprocs=2 -a start_time="2020-08-01" end_time="2021-08-01" \
input=https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2021.nc
```

## TODO

1. Capture and store extended metadata in a way that allows for
    filtering of relevant maps.
2. Improve printing of metadata and file structure
3. Support more options of Virtual Raster files (data type, ...)

## SEE ALSO

*[t.rast.import](https://grass.osgeo.org/grass-stable/manuals/t.rast.import.html),
[r3.out.netcdf](https://grass.osgeo.org/grass-stable/manuals/r3.out.netcdf.html),
[r.semantic\_labels](https://grass.osgeo.org/grass-stable/manuals/r.semantic_labels.html),
[i.bands\_library](https://grass.osgeo.org/grass-stable/manuals/i.bands_library.html),
[r.support](https://grass.osgeo.org/grass-stable/manuals/r.support.html)
[m.crawl.thredds](https://grass.osgeo.org/grass-stable/manuals/addons/m.crawl.thredds.html),*

## AUTHORS

Stefan Blumentrath, [Norwegian Institute for Nature Research (NINA),
Oslo](https://www.nina.no/Kontakt/Ansatte/Ansattinformasjon.aspx?AnsattID=14230)
