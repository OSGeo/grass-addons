## DESCRIPTION

***r.richdem.resolveflats*** imposes a small epsilon gradient on flat areas of a DEM so that every cell has a unique downhill neighbor and a well-defined flow direction. Flat areas---regions in which all cells share the same elevation---commonly arise after depression filling or in gently sloping terrain and prevent the computation of meaningful flow directions.

The algorithm of Barnes et al. (2014) constructs two auxiliary gradient fields and combines them to produce a gradient that drains away from higher terrain and toward lower terrain, ensuring that flow traverses flats in a physically plausible way without crossing drainage divides. The elevation adjustments are on the order of the floating-point epsilon, so they do not meaningfully alter the DEM's topographic properties.

## NOTES

***r.richdem.resolveflats*** is typically applied after *[r.richdem.filldepressions](r.richdem.filldepressions.md)* or *[r.richdem.breachdepressions](r.richdem.breachdepressions.md)* to handle any flat areas created by the conditioning step.

An alternative approach is to use the **-e** flag in *[r.richdem.filldepressions](r.richdem.filldepressions.md)* directly, which combines filling and epsilon-gradient imposition in one step.

This module is not needed before running *[r.richdem.dephier](r.richdem.dephier.md)*, which handles flat areas internally.

## REQUIREMENTS

This module requires the [RichDEM](https://github.com/r-barnes/richdem) Python package, which is not a standard GRASS GIS dependency and must be installed separately:

```bash
pip install richdem
```

If `pip install richdem` fails (the package requires a C++ compiler), build from source:

```bash
git clone https://github.com/r-barnes/richdem.git
cd richdem/wrappers/pyrichdem
pip install -e .
```

Ensure that RichDEM is installed into the same Python environment used by GRASS GIS.

## EXAMPLES

Resolve flat areas after depression filling:

```bash
r.richdem.filldepressions input=dem output=dem_filled
r.richdem.resolveflats input=dem_filled output=dem_conditioned
```

Resolve flats on a raw DEM before computing flow accumulation:

```bash
r.richdem.resolveflats input=dem output=dem_noflats
r.richdem.flowaccumulation input=dem_noflats output=flow_accum
```

## REFERENCES

-   Barnes, R., Lehman, C., Mulla, D. (2014). An efficient assignment of drainage direction over flat surfaces in raster digital elevation models. *Computers & Geosciences* Vol 62, pp 128--135. DOI: [10.1016/j.cageo.2013.01.009](https://doi.org/10.1016/j.cageo.2013.01.009)
-   Barnes, R. (2016). RichDEM: Terrain Analysis Software. URL: <http://github.com/r-barnes/richdem>

## SEE ALSO

*[r.richdem.filldepressions](r.richdem.filldepressions.md), [r.richdem.breachdepressions](r.richdem.breachdepressions.md), [r.richdem.flowaccumulation](r.richdem.flowaccumulation.md), [r.fill.dir](https://grass.osgeo.org/grass-stable/manuals/r.fill.dir.html), [r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

## AUTHORS

Richard Barnes (RichDEM library)

GRASS GIS bindings: Andrew D. Wickert, with assistance from Claude Sonnet 4.6
