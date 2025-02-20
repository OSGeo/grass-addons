## DESCRIPTION

*r.flowaccumulation* calculates flow accumulation from a flow direction
raster map using the Memory-Efficient Flow Accumulation (MEFA) parallel
algorithm by Cho (2023).

## NOTES

Unlike *r.watershed*, but just like *r.accumulate*, *r.flowaccumulation*
does not require elevation data to calculate flow accumulation. Instead,
this module only uses a flow direction raster map to trace and
accumulate the amount of flow draining through and including each cell.

The module recognizes three different formats of flow directions:

![image-alt](r_flowaccumulation_formats.png)

Because it does not use elevation data (e.g., slope), flow accumulation
is calculated by single flow direction (SFD) routing and may not be
comparable to the result from multiple flow direction (MFD) routing.

By default, the module allows cell values to overflow the maximum value
of the specified output **type** to avoid excessive checks. With the
**-o** flag, it prints a fatal error and exits if an overflow occurs.

The module uses extra memory to store an intermediate output matrix and
it is generally faster than with the **-m** flag because intermediate
results need not be calculated repeatedly. On heavy swapping, however,
computation can be faster with the **-m** flag because of reduced memory
allocation. With this flag, intermediate results are calculated as
needed and never stored in memory.

Cells in the output matrix are initialized to null and need not be
nullified after computation. With the **-z** flag, they are initialized
to zero and those outside flow accumulation are nullified later. With
this flag, it can be faster on heavy swapping because of less write
operations for nullifying remaining zero cells outside flow
accumulation, compared to null-initialization of the entire region
without this flag. However, when there is not much swapping (e.g., data
fit in the physical memory), the **-z** flag can be slower with
additional zero-comparison operations. The **-Z** flag is similar to the
**-z** flag, but zero cells are not nullified and are saved in the
output map.

Weighted flow accumulation can be computed using the **weight** option.
When this option is given, the data type for flow accumulation is
automatically promoted to that of the weight map if the **type** option
is not explicitly given, but one can choose to use a different data type
if needed (e.g., FCELL for CELL weights, DCELL for FCELL weights).
However, CELL cannot be used for FCELL or DCELL weighting to maintain
floating-point precision. Similarly, FCELL cannot be used for DCELL
weighting. The data type will be promoted in these cases, ignoring the
user request. The **-o**, **-z**, and **-Z** flags cannot be used with
the **weight** option.

## EXAMPLES

These examples use the North Carolina sample dataset.

Calculate flow accumulation using *r.watershed* and
*r.flowaccumulation*:

```sh
# set computational region
g.region -p raster=elevation

# calculate positive flow accumulation and drainage directions using r.watershed
# for comparison, use -s (SFD)
r.watershed -sa elevation=elevation accumulation=flow_accum drainage=drain_directions

# calculate flow accumulation using r.flowaccumulation
r.flowaccumulation input=drain_directions output=flow_accum_new

# copy color table
r.colors map=flow_accum_new raster=flow_accum

# check difference between flow_accum and flow_accum_new
r.mapcalc expression="flow_accum_diff=if(flow_accum-flow_accum_new, flow_accum-flow_accum_new, null())"
```

![image-alt](r_flowaccumulation_nc_example.png)

There are slight differences between the two output maps. The yellow and
purple cells show the difference raster map (*flow\_accum\_diff*). The
red arrows and numbers represent drainage directions
(*drain\_directions*) and flow accumulation by *r.watershed*
(*flow\_accum*), respectively. Note that some cells close to headwater
cells are assigned 1 even though they are located downstream of other
cells.

![image-alt](r_flowaccumulation_r_watershed_nc_example.png)

For comparison, these numbers show the new flow accumulation by
*r.flowaccumulation* (*flow\_accum\_new*). The same cells are properly
accumulated from the headwater cells.

![image-alt](r_flowaccumulation_nc_comparison.png)

## SEE ALSO

*[r.accumulate](r.accumulate.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.distance](r.stream.distance.md)*

## REFERENCES

Huidae Cho, September 2023. *Memory-Efficient Flow Accumulation Using a
Look-Around Approach and Its OpenMP Parallelization.* Environmental
Modelling & Software 167, 105771.
[doi:10.1016/j.envsoft.2023.105771](https://doi.org/10.1016/j.envsoft.2023.105771).

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com), New Mexico State University
