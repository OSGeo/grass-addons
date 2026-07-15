## DESCRIPTION

*v.in.gps* allows the user to import waypoint, route, and track data
from a locally connected GPS receiver or a text file containing GPS data
of many common formats. Translation is done via the
*[GPSBabel](https://www.gpsbabel.org)* program.

This software is not intended as a primary means of navigation.

## NOTES

*v.in.gps* automatically reprojects data using the projection settings
of the current location. The default input data projection is lat/lon
WGS84. If your GPS outputs data using another projection or map datum,
you may include the *[PROJ](https://proj.org/)* parameters defining your
projection in the **proj** option and *v.in.gps* will reproject your
data accordingly. Great care must be taken to get these parameters
correct\! The automatic transform may be skipped by using the **-k**
flag in which case the data will be imported unprojected, as it appears
in the **input**.

Route and Track data may be uploaded as a series of points by using the
**-p** flag, otherwise they will be imported as lines. You can run
*v.in.gps* multiple times and merge the line and point vectors with the
*v.patch* command if you want, but take care when merging dissimilar
attribute tables.

## EXAMPLES

### GPS device connected via USB adapter

Import waypoints, tracks, routes from /dev/ttyUSB0 and save to a GRASS
vector map:

```sh
v.in.gps -w input=/dev/ttyUSB0 format=garmin output=waypoints
v.in.gps -t input=/dev/ttyUSB0 format=garmin output=tracks
v.in.gps -r input=/dev/ttyUSB0 format=garmin output=routes
```

### GPS device connected via serial adapter

Import waypoint data from a Garmin GPS connected at /dev/ttyS0 and save
to a GRASS vector map named *waypoints*:

```sh
v.in.gps -w input=/dev/ttyS0 format=garmin output=waypoints
```

### Import track data from a GPX

Import track data from a GPX text file and save to a GRASS vector map
named *tracks*.

```sh
v.in.gps -t input=gpslog.gpx format=gpx output=tracks
```

### Import route data from GPS connected at /dev/gps

Import route data as a series of points from a Garmin GPS connected at
/dev/gps and save to a GRASS vector map named *routePoints*:

```sh
v.in.gps -r -p file=/dev/gps format=garmin output=routePoints
```

## SEE ALSO

*[db.execute](https://grass.osgeo.org/grass-stable/manuals/db.execute.html),
[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html),
[v.in.garmin](v.in.garmin.md),
[v.db.connect](https://grass.osgeo.org/grass-stable/manuals/v.db.connect.html),
[v.patch](https://grass.osgeo.org/grass-stable/manuals/v.patch.html)*
[gpsbabel](https://www.gpsbabel.org) from gpsbabel.org  
cs2cs from [PROJ](https://proj.org/)

## AUTHORS

Claudio Porta and Lucio Davide Spano, students of Computer Science at
University of Pisa (Italy).  
Commission from Faunalia Pontedera (PI)  
  
Based on *v.in.garmin* for GRASS 6.0 by Hamish Bowman  
and *v.in.garmin.sh* for GRASS 5 by Andreas Lange
