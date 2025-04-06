## DESCRIPTION

*r.in.usgs* downloads and patches selected USGS datasets (NED, NAIP,
lidar) to the current GRASS computational region and coordinate
reference system. Associated parameters are automatically passed to [The
National Map Access
API](https://viewer.nationalmap.gov/tnmaccess/api/index), downloaded to
a local cache directory, then imported, and patched together.
*r.in.usgs* supports the following datasets:

- **ned**: National Elevation Dataset
- **naip**: NAIP orthoimagery
- **lidar**: Lidar Point Clouds (LPC)

National Land Cover Dataset (NLCD) is no longer available through the
API.

## NOTES

NED data are available at resolutions of 1 arc-second (about 30 meters),
1/3 arc-second (about 10 meters), and in limited areas at 1/9 arc-second
(about 3 meters).

NAIP is available at 1 m resolution.

Lidar data is available only for part of the US but there can be
multiple spatially overlapping datasets from different years. All point
clouds will be imported as points using
[v.in.pdal](https://grass.osgeo.org/grass-stable/manuals/v.in.pdal.html)
and then patched and interpolated with
[v.surf.rst](https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html).
In some cases, lidar point clouds do not have SRS information, use
**input\_srs** to specify it (e.g. "EPSG:2264"). If multiple tiles from
different years are available, use **title\_filter** to filter by their
titles (e.g. "Phase1"). Use **i** flag to list the tiles first.

If the **i** flag is set, only information about data meeting the input
parameters is displayed without downloading the data. If the **d** flag
is set, data is downloaded but not imported and processed.

By default, downloaded files are kept in a user cache directory
according to the operating system standards. These files can be reused
in case a different, but overlapping, computational region is required.
However, unzipped files and imported rasters before patching are
removed. If the **k** flag is set, extracted files from compressed
archives are also kept within the cache directory after the import. The
location of the cache directory depends on the operating system. You can
clear the cache by deleting the directory. Where this directory is
depends on operating system, for example on Linux, it is under
`~/.cache`, on macOS under `~/Library/Caches`, and on Microsoft Windows
under the Application Data directory. If you have limited space or other
special needs, you can set **output\_directory** to a custom directory,
e.g., `/tmp` on Linux. The custom directory needs to exist before
calling this module.

By default, resampling method is chosen based on the nature of the
dataset, bilinear for NED and nearest for NAIP. This can be changed with
option **resampling\_method**.

## EXAMPLE

We will download NED 1/9 arc-second digital elevation model in the
extent of raster 'elevation'. First, we just list the files to be
downloaded:

```sh
g.region raster=elevation
r.in.usgs product=ned ned_dataset=ned19sec output_name=ned -i
```

```text
USGS file(s) to download:
-------------------------
Total download size:    826.95 MB
Tile count: 4
USGS SRS:   wgs84
USGS tile titles:
USGS NED ned19_n35x75_w078x75_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
USGS NED ned19_n36x00_w078x75_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
USGS NED ned19_n35x75_w079x00_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
USGS NED ned19_n36x00_w079x00_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
-------------------------
To download USGS data, remove i flag, and rerun r.in.usgs.
```

We proceed with the download:

```sh
r.in.usgs product=ned ned_dataset=ned19sec output_name=ned
r.colors map=ned_small color=grey
```

We change the computational region to a smaller extent and create a new
DEM, downloaded files will be used.

```sh
g.region n=224649 s=222000 w=633000 e=636000
r.in.usgs product=ned ned_dataset=ned19sec output_name=ned_small
```

For a different extent we download NAIP imagery and we use a custom
cache directory (replace `/tmp` by an existing path suitable for your
operating system and needs):

```sh
g.region n=224649 s=222000 w=636000 e=639000
r.in.usgs product=naip output_directory=/tmp output_name=ortho
```

[![image-alt](r_in_usgs.png)](r_in_usgs.png)  
*Figure: Downloaded NED (large and small extent), NAIP orthoimagery, and
NLCD land cover (NLCD is not available since 2020 through the API)*

## REFERENCES

*[TNM Access API
Guide](https://viewer.nationalmap.gov/help/documents/TNMAccessAPIDocumentation/TNMAccessAPIDocumentation.pdf)  
[National Elevation Dataset](https://nationalmap.gov/elevation.html)  
[National Land Cover Dataset](https://www.mrlc.gov/)*

## SEE ALSO

*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html),
[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html),
[r.colors](https://grass.osgeo.org/grass-stable/manuals/r.colors.html),
[r.in.srtm](https://grass.osgeo.org/grass-stable/manuals/r.in.srtm.html),
[v.in.pdal](https://grass.osgeo.org/grass-stable/manuals/v.in.pdal.html)*

## AUTHORS

Zechariah Krautwurst, 2017 MGIST Candidate, North Carolina State
University  
(initial version, Google Summer of Code 2017, mentors: Anna Petrasova,
Vaclav Petras)

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)  
Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
