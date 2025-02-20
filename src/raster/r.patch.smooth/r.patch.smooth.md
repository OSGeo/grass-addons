## DESCRIPTION

Module fuses rasters representing elevation together by patching them
and smoothing values along edges using either fixed or spatially
variable overlap width. Spatially variable overlap width is given by the
difference along the edge between the two rasters. Higher difference
results in larger overlap width to smooth the transition.

r.patch.smooth can be used, for example, for updating older, lower
resolution DEM (**input\_b**) with newer, higher resolution DEM
(**input\_a**). Note that both DEMs must be aligned and have the same
resolution. Smoothing uses weighted averaging on the overlap of the
rasters. r.patch.smooth supports 2 types of smoothing. The default one
is simpler and uses fixed overlap width defined in **smooth\_dist**.
Since the differences along the seam line can vary, the second option
uses spatially variable overlap width and can be activated with flag
**-s**. The width is then computed based on the elevation differences
along the edge and transition angle **transition\_angle** controlling
the steepness of the transition. If option **overlap** is specified, a
map representing the spatially variable overlap is created and can be
used for inspecting the fusion results.

![image-alt](r_patch_smooth_overview.png)  
Difference between fixed overlap width and spatially variable overlap.

For spatially variable overlap, options **parallel\_smoothing** and
**difference\_reach** can be specified. Option **parallel\_smoothing**
smoothes the overlap zone in direction parallel to the edge. Option
**difference\_reach** enables to increase the sensitivity to higher
differences on the edges by taking maximum difference values in the
cells close to edges.

![image-alt](r_patch_smooth_parallel_smoothing.png)  
Effect of **parallel\_smoothing** option shown on overlap zone (created
by specifying **overlap** option). Image A shows result with value 3 and
B with value 9.

Option **blend\_mask** (experimental) can be used to specify which edges
of the input\_a DEM should be excluded from the blending. This is useful
when DEMs A and B have identical edges (on the coast, for example) and
we want to preserve only A (not blend it with B along the coast). The
**blend\_mask** raster can be created by digitizing area approximately
around the excluded edges, so that the edge of DEM A is inside the areas
and the rest are NULLs. This option requires more testing.

## SEE ALSO

[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.grow.distance](https://grass.osgeo.org/grass-stable/manuals/r.grow.distance.html)

## REFERENCES

Anna Petrasova, Helena Mitasova, Vaclav Petras, Justyna Jeziorska.
[Fusion of high-resolution DEMs for water flow
modeling](https://link.springer.com/article/10.1186/s40965-017-0019-2)
(2017). Open Geospatial Data, Software and Standards. 2: 6.
[DOI: 10.1186/s40965-017-0019-2](https://doi.org/10.1186/s40965-017-0019-2)

## AUTHOR

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
