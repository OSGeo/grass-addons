## DESCRIPTION

*r.richdem* is a collection of seven GRASS GIS modules that expose
algorithms from the [RichDEM](https://github.com/r-barnes/richdem)
terrain-analysis library through standard GRASS raster and vector
interfaces. RichDEM provides high-performance, research-grade algorithms
for hydrological conditioning of digital elevation models (DEMs), flow
routing, and terrain attribute calculation, with particular strength in
handling real topographic depressions rather than removing them.

### Modules

| Module | Description |
| --- | --- |
| [r.richdem.filldepressions](r.richdem.filldepressions.md) | Fill depressions in a DEM using the Priority-Flood algorithm; optional ε-gradient for flat areas |
| [r.richdem.breachdepressions](r.richdem.breachdepressions.md) | Breach depressions by carving least-cost channels (Lindsay 2016) |
| [r.richdem.resolveflats](r.richdem.resolveflats.md) | Impose a local ε-gradient on flat areas to ensure unique flow directions |
| [r.richdem.flowaccumulation](r.richdem.flowaccumulation.md) | Flow accumulation with 13 SFD/MFD algorithms (D8, D-infinity, Quinn, Holmgren, Freeman, ...) |
| [r.richdem.terrainattribute](r.richdem.terrainattribute.md) | Terrain attributes: slope (4 unit systems), aspect, total/planform/profile curvature |
| [r.richdem.dephier](r.richdem.dephier.md) | Compute the depression hierarchy of a DEM (required first step for Fill--Spill--Merge) |
| [r.richdem.fsm](r.richdem.fsm.md) | Fill--Spill--Merge: route surface water through the depression hierarchy without removing depressions |

All modules share a *librichdem* helper library for GRASS ↔ RichDEM raster
and vector conversion, installed to `$GISBASE/etc/r.richdem/librichdem/`.

### Workflows

#### Classic flow-accumulation workflow

Depressions must be removed before computing flow accumulation with most
algorithms. Two approaches:

```bash
# Option A: fill depressions, impose epsilon gradient on flat areas
r.richdem.filldepressions -e input=dem output=dem_filled
r.richdem.flowaccumulation input=dem_filled output=flow_accum

# Option B: breach depressions, resolve remaining flats
r.richdem.breachdepressions input=dem output=dem_breached
r.richdem.resolveflats input=dem_breached output=dem_conditioned
r.richdem.flowaccumulation input=dem_conditioned output=flow_accum method=Dinf
```

#### Fill--Spill--Merge workflow

Fill--Spill--Merge (Barnes et al., 2021) routes water through real
depressions without removing them, producing an equilibrium water-table
depth map. This requires first computing the depression hierarchy:

```bash
# Step 1: build the depression hierarchy (run once per DEM)
r.richdem.dephier input=dem \
    output_labels=dep_labels \
    output_flowdirs=dep_flowdirs \
    output_hierarchy=dep_hierarchy

# Step 2: create an initial water-table depth map
r.mapcalc "wtd = -0.5"

# Step 3: run Fill-Spill-Merge
r.richdem.fsm input=dem \
    labels=dep_labels \
    flowdirs=dep_flowdirs \
    hierarchy=dep_hierarchy \
    water_depth=wtd \
    output=wtd_after
```

## REQUIREMENTS

All modules in this collection require the
[RichDEM](https://github.com/r-barnes/richdem) Python package, which is not
a standard GRASS GIS dependency and must be installed separately:

```bash
pip install richdem
```

If `pip install richdem` fails (the package requires a C++ compiler), build
from source:

```bash
git clone https://github.com/r-barnes/richdem.git
cd richdem/wrappers/pyrichdem
pip install -e .
```

Ensure that RichDEM is installed into the same Python environment used by
GRASS GIS.

## REFERENCES

- Barnes, R., Callaghan, K.L., Wickert, A.D. (2021). Computing water flow
  through complex landscapes -- Part 3: Fill--Spill--Merge: flow routing in
  depression hierarchies. *Earth Surface Dynamics* 9(1), 105--121. DOI:
  [10.5194/esurf-9-105-2021](https://doi.org/10.5194/esurf-9-105-2021)
- Barnes, R., Callaghan, K.L., Wickert, A.D. (2020). Computing water flow
  through complex landscapes -- Part 2: Finding hierarchies in depressions
  and morphological segmentations. *Earth Surface Dynamics* 8(2), 431--445.
  DOI:
  [10.5194/esurf-8-431-2020](https://doi.org/10.5194/esurf-8-431-2020)
- Lindsay, J.B. (2016). Efficient hybrid breaching-filling sink removal
  methods for flow path enforcement in digital elevation models.
  *Hydrological Processes* 30(6), 846--857. DOI:
  [10.1002/hyp.10648](https://doi.org/10.1002/hyp.10648)
- Barnes, R. (2016). RichDEM: Terrain Analysis Software. URL:
  <http://github.com/r-barnes/richdem>

## SEE ALSO

*[r.richdem.filldepressions](r.richdem.filldepressions.md),
[r.richdem.breachdepressions](r.richdem.breachdepressions.md),
[r.richdem.resolveflats](r.richdem.resolveflats.md),
[r.richdem.flowaccumulation](r.richdem.flowaccumulation.md),
[r.richdem.terrainattribute](r.richdem.terrainattribute.md),
[r.richdem.dephier](r.richdem.dephier.md),
[r.richdem.fsm](r.richdem.fsm.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html),
[r.fill.dir](https://grass.osgeo.org/grass-stable/manuals/r.fill.dir.html),
[r.slope.aspect](https://grass.osgeo.org/grass-stable/manuals/r.slope.aspect.html)*

## AUTHORS

Richard Barnes, Kerry L. Callaghan, Andrew D. Wickert
(algorithm design and RichDEM library --- see references above)

GRASS GIS bindings: Andrew D. Wickert, with assistance from Claude Sonnet 4.6
