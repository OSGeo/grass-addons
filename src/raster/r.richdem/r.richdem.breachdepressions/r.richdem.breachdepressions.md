## DESCRIPTION

***r.richdem.breachdepressions*** removes topographic depressions
from a digital elevation model (DEM) by carving a channel from each
pit cell to the nearest drainage outlet, following the
complete-breaching mode of the priority-flood algorithm of Lindsay
(2016) as implemented in RichDEM by Richard Barnes. Unlike
depression filling, which raises interior cells to the pour-point
elevation, breaching lowers the cells along the breach channel,
leaving the surrounding terrain unmodified.

### Algorithm

The algorithm proceeds in three phases:

1. **Initialization.** Each pit cell is *shallowed*: its elevation
   is raised to just below that of its lowest neighbor. This
   removes isolated single-cell pits cheaply and reduces the depth
   and length of breach channels required for larger depressions,
   thereby limiting the algorithm\'s impact on the DEM.
2. **Priority-flood traversal.** DEM edge cells are inserted into
   a min-heap priority queue. The priority of each cell combines
   its elevation and insertion order, which correctly handles flat
   areas without a separate preprocessing step. Cells are removed
   from the queue in priority order; their unvisited neighbors are
   added, and a back-link is recorded for each newly encountered
   cell. When a pit cell is dequeued, the back-link chain is
   traced downslope to find the path to the nearest cell that is
   lower or on the DEM edge. Elevations along that path are
   lowered to form a monotonically descending breach channel.
3. **Output.** In complete-breaching mode all depressions are
   resolved by breaching. (Lindsay (2016) also describes selective
   and constrained hybrid modes that fall back to filling for
   depressions whose breach channel would exceed specified depth or
   length thresholds; those modes are not exposed by this module.)

Complete-breaching processes DEMs in approximately 87% of the time
required by an equivalent depression-filling algorithm
(Lindsay, 2016).

### When to breach versus fill

Breaching is preferred for high-relief landscapes dominated by
fluvial processes, where most depressions are artifacts (erroneous
damming along convergent topography from grid resolution or InSAR
noise). It reinforces natural drainage pathways and modifies fewer
cells than filling.

Filling is preferable for:

- Very deep real depressions --- lakes, wetlands, sinkholes,
  open-pit mines --- where a breach channel would be unrealistically
  long and deeply incised.
- Landscapes where the modelling goal is topographic depression
  mapping rather than surface flow routing.

For landscapes that genuinely contain both artifact and real
depressions, consider the Fill--Spill--Merge workflow
(*[r.richdem.dephier](r.richdem.dephier.md)* +
*[r.richdem.fsm](r.richdem.fsm.md)*), which retains real
depressions and routes water through them explicitly.

### Flow topology

- **D8** (default) --- breach channels connect cells through any
  of the 8 neighbors (including diagonals).
- **D4** --- breach channels connect cells through the 4 cardinal
  neighbors only, producing orthogonal channel paths.

## NOTES

The priority metric used during traversal combines cell elevation
and insertion order using fixed-precision concatenation. This
ensures correct handling of flat areas --- no separate
flat-resolution step is needed after breaching, unlike after
*[r.richdem.filldepressions](r.richdem.filldepressions.md)*
(without the **-e** flag). If flat areas do persist, apply
*[r.richdem.resolveflats](r.richdem.resolveflats.md)* before
computing flow directions or accumulation.

## REQUIREMENTS

This module requires the [RichDEM](https://github.com/r-barnes/richdem)
Python package, which is not a standard GRASS GIS dependency and
must be installed separately:

```bash
pip install richdem
```

If `pip install richdem` fails (the package requires a C++
compiler), build from source:

```bash
git clone https://github.com/r-barnes/richdem.git
cd richdem/wrappers/pyrichdem
pip install -e .
```

Ensure that RichDEM is installed into the same Python environment
used by GRASS GIS.

## EXAMPLES

Breach depressions using D8 topology:

```bash
r.richdem.breachdepressions input=dem output=dem_breached
```

Breach using D4 topology (cardinal neighbors only):

```bash
r.richdem.breachdepressions input=dem output=dem_breached_d4 topology=D4
```

Compare filling versus breaching on the same DEM:

```bash
r.richdem.filldepressions input=dem output=dem_filled
r.richdem.breachdepressions input=dem output=dem_breached
r.mapcalc "diff = dem_filled - dem_breached"
```

## REFERENCES

- Lindsay, J.B. (2016). Efficient hybrid breaching-filling sink
  removal methods for flow path enforcement in digital elevation
  models. *Hydrological Processes* Vol 30(6), pp 846--857. DOI:
  [10.1002/hyp.10648](https://doi.org/10.1002/hyp.10648)
- Barnes, R. (2016). RichDEM: Terrain Analysis Software. URL:
  <http://github.com/r-barnes/richdem>

## SEE ALSO

*[r.richdem.filldepressions](r.richdem.filldepressions.md),
[r.richdem.resolveflats](r.richdem.resolveflats.md),
[r.richdem.flowaccumulation](r.richdem.flowaccumulation.md),
[r.richdem.dephier](r.richdem.dephier.md),
[r.fill.dir](https://grass.osgeo.org/grass-stable/manuals/r.fill.dir.html),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

## AUTHORS

John B. Lindsay (algorithm, Lindsay 2016); Richard Barnes
(RichDEM implementation)

GRASS GIS bindings: Andrew D. Wickert, with assistance from Claude
Sonnet 4.6
