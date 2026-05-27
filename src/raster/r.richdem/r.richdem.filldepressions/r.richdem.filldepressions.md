## DESCRIPTION

***r.richdem.filldepressions*** fills all topographic depressions (pits, sinks) in a digital elevation model (DEM) so that every cell drains to the map boundary. Depression filling is a common pre-processing step before computing flow directions or flow accumulation.

Depressions are raised to the elevation of their lowest outlet (the pour point), producing a hydrologically conditioned DEM in which no interior drainage exists. The algorithm is based on the Priority-Flood approach of Barnes et al. (2014), which runs in optimal O(N log N) time.

When the **-e** flag is set, an epsilon (ε) gradient is imposed on the filled flat areas. This ensures that a unique steepest-descent flow direction exists for every cell, including those within large flat regions created by the fill. Without this flag, filled areas may contain cells with no unique downhill neighbor.

Two flow topologies are supported:

-   **D8** (default) --- each cell drains to one of its 8 neighbors.
-   **D4** --- each cell drains to one of its 4 cardinal neighbors only.

## NOTES

Depression filling removes all interior basins by raising their elevations. This is appropriate when depressions are considered artifacts (e.g., errors in lidar or SRTM data). When depressions represent real landscape features (lakes, prairie potholes, endorheic basins), consider using *[r.richdem.breachdepressions](r.richdem.breachdepressions.md)* or the *[r.richdem.dephier](r.richdem.dephier.md)* / *[r.richdem.fsm](r.richdem.fsm.md)* workflow instead.

After filling, flat regions may be created where the fill raised cells to the same elevation as the pour point. Use the **-e** flag or *[r.richdem.resolveflats](r.richdem.resolveflats.md)* to impose drainage gradients on such areas.

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

Fill depressions using D8 topology:

```bash
r.richdem.filldepressions input=dem output=dem_filled
```

Fill depressions and impose an epsilon gradient on flat areas:

```bash
r.richdem.filldepressions -e input=dem output=dem_filled_eps
```

Fill using D4 topology:

```bash
r.richdem.filldepressions input=dem output=dem_filled_d4 topology=D4
```

## REFERENCES

-   Barnes, R., Lehman, C., Mulla, D. (2014). Priority-flood: An optimal depression-filling and watershed-labeling algorithm for digital elevation models. *Computers & Geosciences* Vol 62, pp 117--127. DOI: [10.1016/j.cageo.2013.04.024](https://doi.org/10.1016/j.cageo.2013.04.024)
-   Barnes, R. (2016). RichDEM: Terrain Analysis Software. URL: <http://github.com/r-barnes/richdem>

## SEE ALSO

*[r.richdem.breachdepressions](r.richdem.breachdepressions.md), [r.richdem.resolveflats](r.richdem.resolveflats.md), [r.richdem.flowaccumulation](r.richdem.flowaccumulation.md), [r.richdem.dephier](r.richdem.dephier.md), [r.fill.dir](https://grass.osgeo.org/grass-stable/manuals/r.fill.dir.html), [r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

## AUTHORS

Richard Barnes (RichDEM library)

GRASS GIS bindings: Andrew D. Wickert, with assistance from Claude Sonnet 4.6
