## DESCRIPTION

*i.sentinel.parallel.download* downloads Sentinel-2 data defined by
scene names in parallel using *i.sentinel.download*.  
If no scene names are specified *i.sentinel.parallel.download* downloads
data for the computational region set in the mapset; i.e, only products
which footprint intersects the current computation region extent (area
of interest, AOI) are selected.

## SEE ALSO

*[i.sentinel](i.sentinel.md) module set,
[i.sentinel.download](i.sentinel.download.md)*

## AUTHOR

Guido Riembauer, [mundialis](https://www.mundialis.de/)
