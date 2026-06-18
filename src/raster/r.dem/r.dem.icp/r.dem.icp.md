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

## REFERENCES

* **ICP framework (point-to-point origin).** Besl, P.J. and McKay, N.D. (1992).
  A method for registration of 3-D shapes. *IEEE Transactions on Pattern
  Analysis and Machine Intelligence*, 14(2), 239-256.
  [doi:10.1109/34.121791](https://doi.org/10.1109/34.121791)
* **Point-to-plane error metric (minimized here).** Chen, Y. and Medioni, G.
  (1992). Object modelling by registration of multiple range images. *Image and
  Vision Computing*, 10(3), 145-155.
  [doi:10.1016/0262-8856(92)90066-C](https://doi.org/10.1016/0262-8856%2892%2990066-C)
* **Projective correspondences (target sampled at the transformed x, y).** Blais,
  G. and Levine, M.D. (1995). Registering multiview range data to create 3D
  computer objects. *IEEE Transactions on Pattern Analysis and Machine
  Intelligence*, 17(8), 820-824.
  [doi:10.1109/34.400574](https://doi.org/10.1109/34.400574)
* **Efficient ICP variants (sampling, rejection, coarse-to-fine).** Rusinkiewicz,
  S. and Levoy, M. (2001). Efficient variants of the ICP algorithm. *Proceedings
  Third International Conference on 3-D Digital Imaging and Modeling (3DIM)*,
  145-152. [doi:10.1109/IM.2001.924423](https://doi.org/10.1109/IM.2001.924423)
* **Linearized least-squares point-to-plane solve.** Low, K.-L. (2004). Linear
  least-squares optimization for point-to-plane ICP surface registration.
  Technical Report TR04-004, Department of Computer Science, University of North
  Carolina at Chapel Hill.
  [PDF](https://www.cs.unc.edu/techreports/04-004.pdf)
* **Trimmed ICP (robust to partial overlap and change).** Chetverikov, D.,
  Stepanov, D. and Krsek, P. (2005). Robust Euclidean alignment of 3D point sets:
  the trimmed iterative closest point algorithm. *Image and Vision Computing*,
  23(3), 299-309.
  [doi:10.1016/j.imavis.2004.05.007](https://doi.org/10.1016/j.imavis.2004.05.007)
* **Robust M-estimator weighting.** Huber, P.J. (1964). Robust estimation of a
  location parameter. *The Annals of Mathematical Statistics*, 35(1), 73-101.
  [doi:10.1214/aoms/1177703732](https://doi.org/10.1214/aoms/1177703732)
* **Convergence analysis of point-to-plane registration.** Pottmann, H., Huang,
  Q.-X., Yang, Y.-L. and Hu, S.-M. (2006). Geometry and convergence analysis of
  algorithms for registration of 3D shapes. *International Journal of Computer
  Vision*, 67(3), 277-296.
  [doi:10.1007/s11263-006-5167-2](https://doi.org/10.1007/s11263-006-5167-2)

## See also

*[r.dem.nk](r.dem.nk.md)*

## Authors

Corey T. White [NCSU GeoForAll Lab](https://geospatial.ncsu.edu/geoforall/)
