## DESCRIPTION

*g.compare.md5* is a module that checks if two GRASS maps are identical.
It uses the MD5 cryptographic hash function. For vector map layers it
does not check if the attribute table(s) are identical, too.

## EXAMPLE

North Carolina example, with elevation map:

```sh
# copy a raster map
g.copy raster=elevation,dem

# now check and return TRUE
g.compare.md5 ainput=elevation binput=dem

# now change the color table
r.colors map=dem color=srtm

# check again and it should return FALSE
g.compare.md5 ainput=elevation binput=dem

# but when adding the -c flag (ignore color table), TRUE is returned
g.compare.md5 -c ainput=elevation binput=dem
```

## AUTHOR

Luca Delucchi, Fondazione Edmund Mach, Research and Innovation Centre,
Department of Biodiversity and Molecular Ecology, [GIS and Remote
Sensing
Unit](https://web.archive.org/web/20151217025426/https://gis.cri.fmach.it/),
Italy
