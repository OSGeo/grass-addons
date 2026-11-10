## DESCRIPTION

*v.in.geopaparazzi* imports all elements saved into Geopaparazzi. The
user can import bookmarks, images (warning for the path to images
depends on Android device), notes (one layer for each category) and
tracks.

## EXAMPLES

To import all the elements in the Geopaparazzi database, use:

```sh
v.in.geopaparazzi -bint database=/path/to/geopaparazzi.db base=mydata
```

To import only the tracks in 3D format

```sh
v.in.geopaparazzi -tz database=/path/to/geopaparazzi.db base=track3d
```

## REFERENCES

[Geopaparazzi](https://www.geopaparazzi.org/)

[Geopaparazzi Tables
schema](http://code.google.com/p/geopaparazzi/wiki/DbTables)

## AUTHOR

Luca Delucchi
