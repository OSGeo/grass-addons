# r.richdem

GRASS GIS add-on collection wrapping the [RichDEM](http://github.com/r-barnes/richdem)
terrain-analysis library.

RichDEM provides fast, research-grade algorithms for hydrological
conditioning of digital elevation models (DEMs), flow routing, and terrain
attribute calculation.
This collection exposes those algorithms as standard GRASS GIS raster and vector
modules, including the full **Fill–Spill–Merge** (FSM) surface-water routing
workflow that retains real depressions rather than filling them.

---

## Modules

| Module | Description |
| --- | --- |
| `r.richdem.filldepressions` | Fill depressions using the Priority-Flood algorithm; optional ε-gradient for flat areas |
| `r.richdem.breachdepressions` | Breach depressions by carving least-cost channels |
| `r.richdem.resolveflats` | Impose a local ε-gradient on flat areas to define unique flow directions |
| `r.richdem.flowaccumulation` | Flow accumulation with 13 SFD/MFD algorithms (D8, D-infinity, Quinn, Holmgren, …) |
| `r.richdem.terrainattribute` | Terrain attributes: slope (4 unit systems), aspect, total/planform/profile curvature |
| `r.richdem.dephier` | Compute the depression hierarchy of a DEM (required first step for FSM) |
| `r.richdem.fsm` | Fill–Spill–Merge: route surface water through the depression hierarchy |

---

## Workflows

### Classic flow-accumulation workflow

Depressions must be removed before computing flow accumulation with most
algorithms. Two approaches:

```bash
# Option A: fill depressions (with epsilon gradient for flat handling)
r.richdem.filldepressions -e input=dem output=dem_filled
r.richdem.flowaccumulation input=dem_filled output=flow_accum

# Option B: breach, then resolve remaining flats
r.richdem.breachdepressions input=dem output=dem_breached
r.richdem.resolveflats input=dem_breached output=dem_conditioned
r.richdem.flowaccumulation input=dem_conditioned output=flow_accum method=Dinf
```

### Fill–Spill–Merge workflow

FSM routes water through real depressions without removing them, producing an
equilibrium water-table depth map from a given water input.

```bash
# Step 1: build the depression hierarchy
r.richdem.dephier input=dem \
    output_labels=dep_labels \
    output_flowdirs=dep_flowdirs \
    output_hierarchy=dep_hierarchy

# Step 2: create an initial water-table depth map
# (negative = water table below surface, e.g. -0.5 m)
r.mapcalc "wtd = -0.5"

# Step 3: run Fill-Spill-Merge
r.richdem.fsm input=dem \
    labels=dep_labels \
    flowdirs=dep_flowdirs \
    hierarchy=dep_hierarchy \
    water_depth=wtd \
    output=wtd_after
```

### Terrain attributes

```bash
r.richdem.terrainattribute input=dem output=slope attribute=slope_degrees
r.richdem.terrainattribute input=dem output=aspect attribute=aspect
r.richdem.terrainattribute input=dem output=planform_curv attribute=planform_curvature
```

---

## Dependencies

- **GRASS GIS** ≥ 8.0
- **RichDEM Python bindings** — specifically the `_richdem` C++ extension
  (part of [RichDEM](http://github.com/r-barnes/richdem)).
  The extension must be built from source and importable in the Python
  environment that GRASS uses.

### Building RichDEM

```bash
git clone https://github.com/r-barnes/richdem.git
cd richdem/wrappers/pyrichdem
pip install -e .   # or: python setup.py build_ext --inplace
```

After building, set `PYTHONPATH` so GRASS can find the extension:

```bash
export PYTHONPATH=/path/to/richdem/wrappers/pyrichdem:$PYTHONPATH
```

> **Note:** If you use a conda environment, activate it *before* starting GRASS
> or ensure that GRASS's Python and the environment where `_richdem` was built
> are the same. Mixing system Python with a conda-linked `libstdc++` can cause
> import errors.

---

## Installation

### From the GRASS GIS Add-ons repository

```bash
g.extension extension=r.richdem
```

Not yet submitted to the official grass-addons repository.

### Manual installation from this repository

```bash
git clone https://github.com/awickert/r.richdem.git
cd r.richdem
make
make install
```

This requires a GRASS GIS development environment (`grass --config path` must
return a valid prefix with `include/Make/` present).

---

## References

Barnes, R., Callaghan, K.L., Wickert, A.D. (2021).
Computing water flow through complex landscapes – Part 3: Fill–Spill–Merge:
flow routing in depression hierarchies.
*Earth Surface Dynamics* 9(1), 105–121.
DOI: [10.5194/esurf-9-105-2021](https://doi.org/10.5194/esurf-9-105-2021)

Barnes, R., Callaghan, K.L., Wickert, A.D. (2020).
Computing water flow through complex landscapes – Part 2: Finding hierarchies
in depressions and morphological segmentations.
*Earth Surface Dynamics* 8(2), 431–445.
DOI: [10.5194/esurf-8-431-2020](https://doi.org/10.5194/esurf-8-431-2020)

Lindsay, J.B. (2016).
Efficient hybrid breaching-filling sink removal methods for flow path
enforcement in digital elevation models.
*Hydrological Processes* 30(6), 846–857.
DOI: [10.1002/hyp.10648](https://doi.org/10.1002/hyp.10648)

Barnes, R. (2016). RichDEM: Terrain Analysis Software.
[http://github.com/r-barnes/richdem](http://github.com/r-barnes/richdem)

---

## License

GPL-3.0. See [LICENSE](LICENSE).

## Authors

Richard Barnes, Kerry L. Callaghan, Andrew D. Wickert
(algorithm design and RichDEM library — see references above)

GRASS GIS bindings: Andrew D. Wickert, with assistance from Claude Sonnet 4.6
