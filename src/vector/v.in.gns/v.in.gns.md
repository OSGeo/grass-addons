## DESCRIPTION

*v.in.gns* imports US-NGA GEOnet Names Server (GNS) country files
(Gazetteer data) into a GRASS vector points map. The country files can
be downloaded from the NGA GNS Web Server (see below). The script
generates a vector point map. Only original files can be processed
(unzip compressed file first). These GNS files are encoded in UTF-8
which is maintained in the GRASS database.

## NOTES

The current DB connection is used to write the database table.

Generally, column names longer that 10 characters are shortened to 10
characters to meet the DBF column name restrictions. If this is a
problem consider choosing another database driver with *db.connect*.

To filter outliers (points outside of a country), the *v.select* module
can be used to perform point-in-polygon tests. *v.select* saves only the
GNS points falling into a country polygon into the new points map.

## SEE ALSO

*[db.connect](https://grass.osgeo.org/grass-stable/manuals/db.connect.html),
[v.select](https://grass.osgeo.org/grass-stable/manuals/v.select.html)*

## REFERENCES

[GEOnet Names Server files for countries and
territories](http://earth-info.nga.mil/gns/html/)  
[Column names explanations](http://earth-info.nga.mil/gns/html/help.htm)

## AUTHOR

Markus Neteler, MPBA Group, ITC-irst, Trento, Italy
