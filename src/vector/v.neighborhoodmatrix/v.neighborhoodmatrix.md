## DESCRIPTION

*v.neighborhoodmatrix* identifies all adjacency relations between
polygons in a vector map and exports these as a 2xn matrix where n is
the number of neighborhood relations with each relation only listed in
one direction (i.e. if a is neighbor of b, the list will contain a,b,
but not b,a) unless the *b* flag is specified. By default, neighbors are
identified by the category numbers. Using the *idcolumn* parameter the
user can define a column to use as identifier of the polygons. If a path
to an output file is specified, the matrix will be written to that file,
otherwise it will be sent to standard output.

## NOTES

Currently the module assumes that the layer above the layer containing
the polygons is empty and available for adding categories to boundaries.
The module uses *v.to.db* to determine neighborhood relations.

## EXAMPLE

Send the neighborhood matrix of the census tracts of the North Carolina
dataset to standard output identifying each tract by its category value:

```sh
v.neighborhoodmatrix in=census_wake2000
```

Idem, but identifying each tract by its STFID code and sending the
output to a file:

```sh
v.neighborhoodmatrix in=census_wake2000 idcolumn=STFID output=census_neighbors.csv
```

## SEE ALSO

*[v.to.db](https://grass.osgeo.org/grass-stable/manuals/v.to.db.html)*

## AUTHOR

Moritz Lennert
