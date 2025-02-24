## DESCRIPTION

This module implements Mblend, a DEM merging method proposed by Leitão
*et al.* (2016). It deals with cases where a study area is only
partially covered by a high resolution DEM, with a coarser DEM available
for the remainder (as in the case shown below). *r.mblend* merges the
two DEMs, producing a smooth transition from the high resolution DEM to
the low resolution DEM.  
  
![image-alt](both_inputs.png)  
  
The module works by identifying the edge between the two rasters (near
edge, shown in read below) and the edge composed by the cells in the low
resolution DEM farther away from the high resolution raster (far edge,
shown in blue below). To each point along the near edge is assigned the
difference between the two DEMs. To each point in the far edge is
assigned the value 0. The Inverse Distance Weighted (IDW) method is then
used to interpolate a new raster with the points along the two edges.
This interpolated differences raster thus trends from the full
difference at the near edge towards zero at the far edge.  
  
![image-alt](edges.png)  
  
The differences raster is finally added to the low resolution DEM given
as input. In the resulting DEM, cells along the near edge take the
values in the high resolution raster. The farther away from the near
edge (and closer to to the far edge) the closer is their value is to the
low resolution raster, producing a smooth transition, without
artefacts.  
  
![image-alt](blended.png)

## EXAMPLES

Merge the `best_dem` and `other_dem` raster maps from the current
mapset:

```sh
r.mblend high=best_dem low=other_dem output=result
```

Modifying the far edge distance cut-off:

```sh
r.mblend high=best_dem low=other_dem output=result far_edge=90
```

## REFERENCES

J.P. Leitão, L.M. de Sousa, [Towards the optimal fusion of
high-resolution Digital Elevation Models for detailed urban flood
assessment](https://doi.org/10.1016/j.jhydrol.2018.04.043), *Journal of
Hydrology*, Volume 561, June 2018, Pages 651-661, DOI:
[10.1016/j.jhydrol.2018.04.043](https://doi.org/10.1016/j.jhydrol.2018.04.043).
  
L.M. de Sousa, J.P. Leitão, [Improvements to DEM Merging with
r.mblend](http://www.scitepress.org/PublicationsDetail.aspx?ID=mcJr0zto14w=&t=1).
In *Proceedings of the 4th International Conference on Geographical
Information Systems Theory, Applications and Management - Volume 1:
GISTAM*, March 2018, pages 42-49. ISBN 978-989-758-294-3 DOI:
[10.5220/0006672500420049](https://doi.org/10.5220/0006672500420049).  
  
J.P. Leitão, D. Prodanovic, C. Maksimovic, [Improving merge methods for
grid-based digital elevation
models](https://www.sciencedirect.com/science/article/abs/pii/S0098300416300012),
*Computers & Geosciences*, Volume 88, March 2016, Pages 115-131, ISSN
0098-3004, DOI:
[10.1016/j.cageo.2016.01.001](https://doi.org/10.1016/j.cageo.2016.01.001).

## AUTHORS

Luís Moreira de Sousa  
ISRIC - World Soil Information  
João Paulo Leitão  
EAWAG: Swiss Federal Institute of Aquatic Science and Technology.
