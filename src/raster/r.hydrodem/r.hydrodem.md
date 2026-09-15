## DESCRIPTION

*r.hydrodem* applies hydrological conditioning (sink removal) to a
required input *elevation* map. If the conditioned elevation map is
going to be used as input elevation for *r.watershed*, only small sinks
should be removed and the amount of modifications restricted with the
**mod** option. For other modules such as *r.terraflow* or third-party
software, full sink removal is recommended.

## OPTIONS

- **input**  
    Input map, required: Digital elevation model to be corrected. Gaps
    in the elevation map that are located within the area of interest
    should be filled beforehand, e.g. with *r.fillnulls* or
    *r.resamp.bspline*, to avoid distortions.
- **output**  
    Output map, required: Hydrologically conditioned digital elevation
    model. By default, only minor modifications are done and not all
    sinks are removed.
- **size**  
    All sinks of up to **size** cells will be removed. Default is 4, if
    in doubt, decrease and not increase.
- **mod**  
    All sinks will be removed that require not more than **mod** cells
    to be modifed. Often, rather large sinks can be removed by carving
    through only few cells. Default is 4, if in doubt, increase and not
    decrease.
- **-a**  
    **Not recommended if input for *r.watershed* is generated.**  
    With the **-a** flag set, all sinks will be removed using an impact
    reduction approach based on Lindsay & Creed (2005). The output will
    be a depression-less digital elevation model, suitable for e.g.
    *r.terraflow* or other hydrological analyses that require a
    depression-less DEM as input.

## NOTES

This module is designed for *r.watershed* with the purpose to slightly
denoise a DEM prior to analysis. First, all one-cell peaks and pits are
removed, then the actual hydrological corrections are applied. In most
cases, the removal of one-cell extrema could already be sufficient to
improve *r.watershed* results in difficult terrain, particularly nearly
flat areas.

The impact reduction algorithm used by *r.hydrodem* is based on Lindsay
& Creed (2005), with some additional checks for hydrological
consistency. With complete sink removal, results of *r.terraflow* are
very similar to results of *r.watershed*.

*r.hydrodem* uses the same method to determine drainage directions like
*r.watershed*.

## REFERENCES

Lindsay, J. B., and Creed, I. F. 2005. Removal of artifact depressions
from digital elevation models: towards a minimum impact approach.
Hydrological Processes 19, 3113-3126. DOI:
[10.1002/hyp.5835](https://doi.org/10.1002/hyp.5835)

## SEE ALSO

*[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html),
[r.terraflow](https://grass.osgeo.org/grass-stable/manuals/r.terraflow.html),
[r.fill.dir](https://grass.osgeo.org/grass-stable/manuals/r.fill.dir.html),
[r.fillnulls](https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html),
[r.resamp.bspline](https://grass.osgeo.org/grass-stable/manuals/r.resamp.bspline.html)*

## AUTHOR

Markus Metz
