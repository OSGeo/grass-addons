## DESCRIPTION

*r.buildvrt.gdal* builds GDAL virtual rasters over GRASS GIS raster maps
and links them to the mapset with *r.external*. The module is written as
a workaround for a limitation in GRASS GIS Virtual Rasters (VRT) format
with GDAL-linked raster maps (through *r.external* / *r.external.out*.
In that case GRASS GIS Virtual Rasters currently show performance
issues. See: [\#4345](https://github.com/OSGeo/grass/issues/4345)

For the resulting maps GDAL VRT text files are created either in a
directory named "gdal" in the current mapset or in a user-defined
**vrt\_directory**. Those files are not removed when the raster map is
removed and the user is responsible for removing them when needed.

## REQUIREMENTS

*r.buildvrt.gdal* uses the Python bindings for
[GDAL](https://pypi.org/project/GDAL) and requires the GDAL-GRASS driver
to include raster maps in native GRASS format in GDAL VRTs.

## EXAMPLES

```sh
# Create external example data
regs='s,0,1000
n,500,1500'

eval `g.gisenv`
external_path="${GISDBASE}/${LOCATION}/${MAPSET}/.tmp/vrt"
mkdir -p "$external_path"
for reg in $regs
do
  r=$(echo $reg | cut -f1 -d",")
  s=$(echo $reg | cut -f2 -d",")
  n=$(echo $reg | cut -f3 -d",")

  g.region -g n=$n s=$s w=0 e=1000 res=1
  r.external.out format=GTiff options="compress=LZW,PREDICTOR=3" \
    directory="$external_path"
  r.mapcalc --o --v expression="${r}_${s}_gtiff_ntfs=float(x()*y())"
done

# Run performance tests
g.region -g n=1500 s=0 w=0 e=1000 res=1
format_type=gtiff_ntfs
rmaps=$(g.list type=raster pattern="*_*_${format_type}", sep=",")

# Using GRASS GIS VRT
r.buildvrt --o --v input="$rmaps" output=vrt_${format_type}
time r.univar map=vrt_${format_type}

# Using GDAL VRT
r.buildvrt.gdal --o --v input="$rmaps" output=vrt_${format_type}_gdal
time r.univar map=vrt_${format_type}_gdal
```

## SEE ALSO

*[r.buildvrt](https://grass.osgeo.org/grass-stable/manuals/r.buildvrt.html),
[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html),
[r.external](https://grass.osgeo.org/grass-stable/manuals/r.external.html),
[r.external.out](https://grass.osgeo.org/grass-stable/manuals/r.external.out.html)*

## AUTHORS

Stefan Blumentrath
