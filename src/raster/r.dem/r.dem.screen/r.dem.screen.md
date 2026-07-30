## DESCRIPTION

*r.dem.screen* performs a rapid regional triage that fuses topographic change
(from a DEM of Difference) with optional spectral change (NDVI or VARI), and can
overlay the result with infrastructure to flag hazard hotspots. It is intended
as a coarse-resolution first pass that directs detailed analysis toward the
highest-priority areas.

### Triage

The **output** raster classifies each cell into a priority class. With a
**spectral_change** raster supplied:

| Class | Meaning |
| ------- | --------- |
| 0 | No significant change |
| 1 | Spectral change only (vegetation damage) |
| 2 | Topographic change only (geomorphic) |
| 3 | Topographic and spectral change (highest priority) |

A cell is flagged for topographic change when `|dod| >= topo_threshold`, and for
spectral change when `spectral_change <= spectral_threshold` (negative values
indicate vegetation loss). Without a spectral input only topographic change is
classified (classes 0 and 2).

### Hazard overlay

When both an **infrastructure** vector and a **hazard_output** name are given,
the infrastructure is buffered by **infra_buffer_m** and intersected with the
triage result:

| Class | Meaning |
| ------- | --------- |
| 0 | No change and no infrastructure |
| 1 | Infrastructure, no change detected |
| 2 | Change detected, no infrastructure |
| 3 | CRITICAL: change intersects infrastructure |

## NOTES

The tool reports per-class cell counts and areas. Both outputs carry category
labels. Run the tool at the regional screening resolution (for example 10 m);
the **dod** input is expected to be a significant-change raster, such as the
significant DoD from *r.dem.change*.

## EXAMPLES

Topographic and spectral triage:

```sh
r.dem.screen dod=dod_sig_10m spectral_change=ndvi_change \
    output=triage_10m topo_threshold=1.0 spectral_threshold=-0.15
```

Add an infrastructure hazard overlay:

```sh
r.dem.screen dod=dod_sig_10m spectral_change=ndvi_change \
    output=triage_10m infrastructure=roads \
    hazard_output=hazard_10m infra_buffer_m=30
```

## SEE ALSO

*[r.dem](r.dem.md)*,
*[r.dem.change](r.dem.change.md)*,
*[r.dem.errprop](r.dem.errprop.md)*,
*[v.buffer](v.buffer.md)*,
*[v.to.rast](v.to.rast.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
