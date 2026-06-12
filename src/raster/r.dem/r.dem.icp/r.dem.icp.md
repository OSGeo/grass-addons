## Description

**r.dem.icp** - Rigid (3D or 4-DoF constrained) co-registration of two DEM rasters.

* Point‑to‑plane ICP with projective correspondences (sample target DEM at
transformed (x, y))
* Multiscale (coarse→fine) via adjustable sampling stride
* Trimmed ICP (keep best residual fraction) + Huber robust weighting
* OpenMP parallelization of main loops
* DEM‑specific: normals from DEM gradients; optional slope limit;
optional stable‑terrain mask

## Examples

```bash
g.region raster=reference_dem
r.dem.icp reference=reference_dem source=source_dem output=aligned_dem \
  mask=stable_mask dof=4 levels=3 stride=2 max_iterations=30 trim=0.8 huber=1.0 \
  tolerance=1e-5 distance_max=10 slope_max=90 \
  init_dx=0 init_dy=0 init_dz=0 init_yaw=0 \
  transform_out=transform.txt stats_out=stats.txt
```

## Notes

* **Initialization:** If you already know an approximate horizontal shift or
yaw (e.g., from metadata or phase correlation), pass it via `init_*`.
A good `init_dz` is often the **median** of `(source - reference)` over stable terrain.
* **Speed knobs:** Increase `stride` and reduce `levels` for quick tests;
relax `max_iterations`.
* **Robustness:** Use a conservative `trim` (0.6–0.9). If many changes
(landslides/forest canopy), lower `trim` and/or `huber`.
* **Constraints:** 4‑DoF (`dof=4`) is the supported mode and usually suffices
(e.g., airborne photogrammetry vs LiDAR). **6‑DoF (`dof=6`) is experimental:**
the rigid roll/pitch rotation is ill‑conditioned for height‑field DEMs and its
resample is approximate. To correct a vertical **tilt** between two DEMs, run
*[r.dem.nk](r.dem.nk.md)* (Nuth & Kääb) after ICP rather than using 6‑DoF.
* **Validation:** After alignment, inspect the residual DoD and the stats file;
residual bias should be \~0 on stable terrain.

## See also

*[r.dem.nk](r.dem.nk.md)*

## Authors

Corey T. White [NCSU GeoForAll Lab](https://geospatial.ncsu.edu/geoforall/)

## References

* Original ICP (point-to-point): Besl & McKay, IEEE TPAMI, 1992.
* Point-to-plane ICP: Chen & Medioni, 1991; and a clear derivation in Low
* Efficient ICP variants (sampling, rejection, solvers): Rusinkiewicz & Levoy, 2001.
* Trimmed ICP (robust to partial overlap/change): Chetverikov et al., 2002.
* Generalized ICP (probabilistic, often best in practice): Segal, Haehnel &
Thrun, RSS 2009.
