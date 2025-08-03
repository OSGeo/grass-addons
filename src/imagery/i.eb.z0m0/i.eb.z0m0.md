## DESCRIPTION

*i.eb.z0m0* calculates the momentum roughness length (z0m) and
optionally the surface roughness for heat transport (z0h) as per SEBAL
requirements from bastiaanssen (1995). This version is calculating from
a NDVI with an deterministic equation, as seen in Bastiaanssen (1995).
This is a typical input to sensible heat flux computations of any energy
balance modeling.

## NOTES

The NDVI map input and the ndvi\_max operation set, is only to get a
linear relationship from NDVI to vegetation height. The latter being
related to z0m by a factor 7. If you happen to have a vegetation height
(hv) map, then z0m=hv/7 and z0h=0.1\*z0m. There, fixed.

## TODO

## SEE ALSO

*[i.eb.h0](i.eb.h0.md), [i.eb.h\_SEBAL95](i.eb.h_SEBAL95.md),
[i.eb.h\_iter](i.eb.h_iter.md), [i.eb.z0m](i.eb.z0m.md)*

## AUTHOR

Yann Chemin, International Rice Research Institute, The Philippines
