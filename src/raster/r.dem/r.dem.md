# r.dem — GRASS Toolbox for Topographic Change Analysis

## Tools

| Addon | Description | Status |
| --- | --- | --- |
| `r.dem.coregister` | PGCP vertical bias correction + optional N&K/ICP | implemented |
| `r.dem.nk` | Nuth & Kääb (2011) horizontal and vertical co-registration | implemented |
| `r.dem.icp` | ICP point-to-plane point cloud co-registration | implemented |
| `r.dem.bias` | Terrain-regression and forest-bump systematic bias removal | implemented |
| `r.dem.stats` | Terrain surface metrics (slope, roughness, diversity, local sigma) | implemented |
| `r.dem.errprop` | Uncertainty propagation, LoD, t/p significance, categorical classes | implemented |
| `r.dem.lod` | Level of Detection with global and local uncertainty modes | implemented |
| `r.dem.change` | DoD computation, LoD masking, volumetric summary | implemented |
| `r.dem.screen` | 10 m screening with topo, spectral, and infra overlays | implemented |
<!-- | `r.dem.floodrisk` | Flood-risk products from terrain change | planned |
| `r.dem.report` | Automated field-printable PDF report generation | planned | -->

DoD computation, cleanup, LoD masking, and volumetric summary all live in
`r.dem.change` as a single pipeline; there is no separate `r.dem.dod` tool.

The alignment tools (`r.dem.coregister`, `r.dem.nk`, `r.dem.icp`) remove rigid
offset and rotation. `r.dem.bias` then removes terrain-correlated systematic
bias that survives alignment. `r.dem.stats` supplies the terrain predictors that
`r.dem.bias` and `r.dem.errprop` consume.

---

## Installation

```bash
# From GRASS addon repository (once published):
g.extension extension=r.dem

# Or install from local source:
g.extension extension=r.dem url=/path/to/r.dem
```

## Citation

White, C. et al. (in prep). Post-Hurricane Topographic Change Assessment Using
Civil Air Patrol Aerial Imagery and Structure-from-Motion Photogrammetry.
*Remote Sensing* (MDPI), Special Issue: Application of Digital Aerial
Photogrammetry in Geomorphological Studies.
