## DESCRIPTION

*i.eb.z0m* calculates the momentum roughness length (z0m) and optionally
the surface roughness for heat transport (z0h) as per SEBAL requirements
from Bastiaanssen (1995). Default: calculating from a NDVI with an
deterministic equation, as seen in Bastiaanssen (1995). Flag -p :
calculating from a SAVI with an empirical equation, as seen in Pawan
(2004). This is a typical input to sensible heat flux computations of
any energy balance modeling.

## NOTES

The NDVI map input and the ndvi\_max operation set, is only to get a
linear relationship from NDVI to vegetation height. The latter being
related to z0m by a factor 7. If you happen to have a vegetation height
(hv) map, then z0m=hv/7 and z0h=0.1\*z0m.

## TODO

## SEE ALSO

*[i.eb.h0](i.eb.h0.md)*

## REFERENCES

- Bastiaanssen, W.G.M., 1995. Regionalization of surface flux
    densities and moisture indicators in composite terrain; a remote
    sensing approach under clear skies in mediterranean climates. PhD
    thesis, Wageningen Agricultural Univ., The Netherland, 271 pp.
    ([PDF](https://edepot.wur.nl/206553))
- Chemin, Y., 2012. A Distributed Benchmarking Framework for Actual ET
    Models, in: Irmak, A. (Ed.), Evapotranspiration - Remote Sensing and
    Modeling. InTech.
    ([PDF](https://www.intechopen.com/books/evapotranspiration-remote-sensing-and-modeling/a-distributed-benchmarking-framework-for-actual-et-models),
    [DOI: 10.5772/23571](https://doi.org/10.5772/23571))

## AUTHOR

Yann Chemin
