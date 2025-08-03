## DESCRIPTION

*v.faultdirections* draws a polar barplot of fault directions, with
values binned according to the *step* parameter. Directions have to be
stored in an attribute column of the vector map containing the faults.

The parameter *legend\_angle* allows positioning the radial axis. By
setting the flag *a* the user can choose to display absolute number of
lines as radial axis labels instead of the default percentages.

## NOTES

The module
[v.to.db](https://grass.osgeo.org/grass-stable/manuals/v.to.db.html) can
be used to load azimuth directions into the attribute table.

The plot can be saved to a graphics file interactively from the
matplotlib window.

## DEPENDENCIES

This module depends on matplotlib and on tkinter (aka python-tk). It is
the users responsibility to make sure both are installed.

## EXAMPLE

Load azimuth directions into the attribute map and draw plot:

```sh
v.db.addcolumn faultmap col="azimuth double precision"
v.to.db faultmap option=azimuth colum=azimuth
v.faultdirections faultmap column=azimuth step=10
```

## SEE ALSO

*[v.to.db](https://grass.osgeo.org/grass-stable/manuals/v.to.db.html)*

## AUTHOR

Moritz Lennert
