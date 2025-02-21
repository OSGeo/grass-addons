## DESCRIPTION

*v.fixed.segmentpoints* creates segment points along a vector line with
fixed distances by using the *v.segment* module. A category of one line
has to be given. Start and end point of the line will be considered. The
distance option is limited to an integer number. As a *prefix* (starting
with a letter) has to be given, resulting vectors are
*prefix*\_singleline and *prefix*\_segmentpoints, resulting external
files are *prefix*\_segmentpoints and *prefix*\_segmentpoints.csv.

The next to last point may be closer to the last point as the given
distance. Distance information for every point is added to the vector
attribute table. The attribute is then exported as CSV file. The
*category (cat)* of the input line is stored in the column *cat\_line*
of the *prefix*\_segmentpoints attribute table.

## EXAMPLE

```sh
  # NC sample data set
  v.fixed.segmentpoints vector=streams@PERMANENT cat=40102 dir=C:\tmp distance=25
 
```

## DEPENDENCIES

- v.segment

## SEE ALSO

*[v.segment](https://grass.osgeo.org/grass-stable/manuals/v.segment.html)*

## AUTHOR

Helmut Kudrnovsky
