## DESCRIPTION

*i.eb.deltat* calculates the difference of temperature between two
heights. Generally considered between surface skin temperature and air
temperature \~2m above the skin (soil/canopy/etc). This approximation is
found in Pawan (2004) and is used for initialization of the sensible
heat flux iterations in SEBAL (Bastiaanssen, 1995).

## NOTES

This is found in Pawan (2004). This is the case of a Landsat satellite
image of Oct 8, 2003, located in Portugal. He also mentions a strange
equation for MODIS of January 13, 2003. delta T = -3440.37 +12.18404 \*
LST. Of course the intercept looks like the LST band is still in storage
format (\*10000). Additionally, it is worth menitoning that Pawan only
created this map once, and used it all the time. This is certainly
because he created the relationship from some field data and found it
reliable enough not to modify this parameter anymore, leading to a
simplified iteration process of SEBAL, changing only the rah parameter
through the iterations of H,L,psi,rah.

## TODO

## SEE ALSO

*[i.eb.h0](i.eb.h0.md)*

## AUTHOR

Yann Chemin, Asian Institute of Technology, Thailand
