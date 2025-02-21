[![image-alt](grass_logo.png)](https://grass.osgeo.org/grass-stable/manuals/index.html)

-----

## NAME

The *r.green.hydro* - Toolset for computing the hydropower potential.

## KEYWORDS

[raster](https://grass.osgeo.org/grass-stable/manuals/raster.html),
[biomass
topic](https://grass.osgeo.org/grass-stable/manuals/topic_biomass.html)

## DESCRIPTION

The *r.green.hydro* suite computes the hydropower potential.  
It is composed of several programs considering different limits (e.g.
theoretical, recommended, legal, technical, ecological and economic
constraints).  
The *r.green.hydro* suite consists of the following six different
parts:  
  
\- [r.green.hydro.theoretical](r.green.hydro.theoretical.md)  
calculates for each basin the theoretical maximum hydropower energy
potential  
input raster maps:    - discharge along river network     - elevation of
the considered region  
input vector map:       existing plant position  
output vector maps: - available river segments               - optimal
plant position  
  
\- [r.green.hydro.recommended](r.green.hydro.recommended.md)  
detects the potential plant position considering legal and ecological
constraints and the user's recommendations  
input raster maps:    - discharge along river network     - elevation of
the considered region     - minimum flow discharge  
input vector maps:    - existing plant position                   -
areas excluded from calculation  
output vector maps: - available river segments               - optimal
plant position  
  
\- [r.green.hydro.technical](r.green.hydro.technical.md)  
calculates the hydropower potential considering technical constrains
(head losses, efficiency of turbine)  
input vector map:       intakes and restitutions of the potential
plants  
output vector map:  - structure (derivation channel and penstock) on
both sides of the river for each potential plant  
  
\- [r.green.hydro.financial](r.green.hydro.financial.md)  
computes the economic costs and values of the plants  
input raster maps:    - landuse     - slope  
input vector maps:   - segments of the potential plants   - plant
structure     - electric grid  
output vector map:    structure of the potential plants with a
re-organized table with e.g. power, gross head, total cost  
  
\- [r.green.hydro.structure](r.green.hydro.structure.md)  
computes the derivation channel and the penstock for each potential
plant on both sides of the river  
input raster map:       elevation of the considered region  
input vector map:       segments of the potential plants  
output vector map:    structure for each plant on both sides of the
river  
  
\- [r.green.hydro.optimal](r.green.hydro.optimal.md)  
detects the position of the potential hydropower plants that can produce
the highest possible power  
input raster maps:    - discharge along river network     - elevation of
the considered region  
input vector map:       considered rivers  
output vector maps: - potential river segments               - intake
and restitution of each potential plant  
  
## SEE ALSO

*[r.green](r.green.md) - overview page*

## AUTHOR

For authors and references, please refer to the respective modules of
*r.green*.
