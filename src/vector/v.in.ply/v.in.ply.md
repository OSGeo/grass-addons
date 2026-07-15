## DESCRIPTION

*v.in.ply* imports a vector map in PLY vector format. A PLY file always
holds a number of vertices which are imported as points. PLY vertices
can have a number of properties in addition to their coordinates. These
properties are stored in an attribute table. For larger PLY files with
many vertices (\> 1000) it is highly recommended to not use DBF as
database driver, but SQLite (default in GRASS GIS 7), PostgreSQL or
MySQL, because the DBF driver is rather slow and can consume a lot of
memory. The database driver can be set with *db.connect*.

## NOTES

*v.in.ply* is designed for large point clouds with the possibility to
have only coordinates, and no attribute table (for speed reasons).

## EXAMPLES

```sh
v.in.ply input=myfile.ply output=myfile
```

## REFERENCES

<https://paulbourke.net/dataformats/ply>  
<https://sites.cc.gatech.edu/projects/large_models/ply.html>

## AUTHOR

Markus Metz
