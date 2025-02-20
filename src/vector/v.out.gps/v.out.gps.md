## DESCRIPTION

*v.out.gps* allows the user to export waypoint, route, and track data
from a vector map into a locally connected GPS receiver or as a file in
many common GPS data formats. Translation is done via the
*[GPSBabel](https://www.gpsbabel.org)* program.

Do not use as a primary means of navigation. This program is distributed
in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE. See the GNU General Public License (GPL) for more details.

## NOTES

*v.out.gps* automatically reprojects data from the projection settings
of the current location to Lat/Lon WGS84.

GPX format is used for data interchange between GRASS and GpsBabel. If
the requested output is GPX, then `gpsbabel` is never run.

OGR's GPX driver knows a number of standard field names. If an attribute
column matches the name it will be used in that field. Otherwise the
attribute will be placed within the `<extensions>` metadata section of
the record. Not all fields names are used with all feature types (e.g.
DOP fix error is not meaningful for route lines). You can use the
*v.db.renamecolumn* module to rename columns.

These are the standard GPX data fields known to OGR:

```sh
ageofdgpsdata
cmt:     Comment
course
desc
dgpsid:  DGPS station type
ele:     Elevation
fix
geoidheight
hdop:    Horizontal dillution of precision (estimated fix error)
magvar:  Magnetic variation
name
number
pdop:    Positional dillution of precision (estimated fix error)
route_fid
route_point_id
sat
speed
src
sym
time
track_fid
track_seg_id
track_seg_point_id
type
url
urlname
vdop:    Vertical dillution of precision (estimated fix error)
```

## EXAMPLES

### GPX Export

Export a vector lines map to a GPX track file:

```sh
v.out.gps -t input=trail output=trail.gpx
```

### GPS device connected via USB adapter

Export vector maps named *waypoints, tracks, routes* to a Garmin GPS
connected to /dev/ttyUSB0:

```sh
v.out.gps -w input=waypoints format=garmin output=/dev/ttyUSB0
v.out.gps -t input=tracks format=garmin output=/dev/ttyUSB0
v.out.gps -r input=routes format=garmin output=/dev/ttyUSB0
```

## SEE ALSO

*[m.proj](https://grass.osgeo.org/grass-stable/manuals/m.proj.html),
[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html),
[v.out.ascii](https://grass.osgeo.org/grass-stable/manuals/v.out.ascii.html),
[v.db.renamecolumn](https://grass.osgeo.org/grass-stable/manuals/v.db.renamecolumn.html),
[v.extract](https://grass.osgeo.org/grass-stable/manuals/v.extract.html)*

[GpsBabel.org](https://www.gpsbabel.org)  
The [GDAL/OGR GPX format
page](https://gdal.org/drivers/vector/gpx.html)  
cs2cs from [PROJ.4](https://proj.org)  

## AUTHOR

Hamish Bowman, Dunedin, New Zealand
