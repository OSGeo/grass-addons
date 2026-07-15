## DESCRIPTION

*r.tpi*calculates a multiscale version of the Topographic Position Index
(TPI) of Guisan et al. (1999). The TPI is calculated by averaging a DEM
over a user-specified moving window size and subtracting the original
DEM from the averaged version to get the residual. This has the effect
of extracting finer-scale landforms from regional-scale relief. Positive
TPI values represent ridges or hills, and negative TPI values represent
valleys or pits.

Unlike the original TPI, *r.tpi* implements a multiscale version that
calculates a standardized TPI over multiple neighborhood radii from
*minradius* to *maxradius*, starting at the largest neighborhood size.
For subsequent steps, the standardized TPI is updated with pixels where
the absolute TPI values exceed the TPI values of the previous step. For
large neighborhoods \> 15, resampling is used rather than a focal
function to generalize the DEM.

## EXAMPLE

```sh
g.region raster=elevation@PERMANENT -a
r.tpi input=elevation@PERMANENT minradius=1 maxradius=25 steps=5 output=tpi
```

![image-alt](r_tpi.png)

## REFERENCES

Guisan, A., S. B. Weiss, A. D. Weiss 1999. GLM versus CCA spatial
modeling of plant species distribution. Plant Ecology 143: 107-122

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),*

## AUTHOR

Steven Pawley
