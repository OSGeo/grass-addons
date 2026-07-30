## DESCRIPTION

*r.dem.lod* computes a Level of Detection (LoD) raster for DEM differencing,
the elevation-change magnitude below which a measured difference cannot be
distinguished from noise. It supports a **global** (spatially uniform) and a
**local** (spatially variable) mode.

The uncertainty of the difference is estimated from the Normalized Median
Absolute Deviation (NMAD) of the elevation residuals on stable terrain:

```text
NMAD = 1.4826 * median(|dh - median(dh)|)
LoD  = t * sqrt(2) * sigma
```

where `sigma = NMAD / 1.4826`, `dh = dem - reference`, and `t` is the two-tailed
normal critical value for the requested **confidence** level.

### method=global

A single NMAD is estimated over the whole study area (or the **stable_mask**
region when supplied), producing a uniform LoD value applied everywhere.

### method=local

A spatially variable LoD is computed in a moving window of size **window**:

```text
sigma_local(x,y) = 1.4826 * median(|dh - median(dh)|)  in window W
LoD(x,y)         = t * sqrt(2) * sigma_local(x,y)
```

When a **point_density** raster is supplied, the local uncertainty is penalised
in sparsely sampled areas before the LoD is computed.

## NOTES

A precomputed **nmad** value can be supplied to skip the stable-pixel
estimation, and a **stable_mask** restricts the residual statistics to terrain
assumed unchanged (roads, parking lots, bare ground).

The output LoD raster can be passed directly to *r.dem.change* as the **lod**
input for significance thresholding. For full per-source uncertainty
propagation (combining several error rasters in quadrature) use
*r.dem.errprop*.

The tool requires the Python *scipy* package.

## EXAMPLES

Global LoD at 95% confidence over a stable mask:

```sh
r.dem.lod dem=dem_post reference=dem_pre output=lod_global \
    method=global confidence=0.95 stable_mask=stable
```

Local LoD in a 21-cell window with a point-density penalty:

```sh
r.dem.lod dem=dem_post reference=dem_pre output=lod_local \
    method=local window=21 point_density=pts_per_m2 confidence=0.95
```

## REFERENCES

- Wheaton et al. (2010), *Earth Surface Processes and Landforms* 35:136-156.
- Hoehle and Hoehle (2009), *ISPRS J. Photogramm. Remote Sens.* 64:398-406.

## SEE ALSO

*[r.dem](r.dem.md)*,
*[r.dem.change](r.dem.change.md)*,
*[r.dem.errprop](r.dem.errprop.md)*,
*[r.dem.stats](r.dem.stats.md)*,
*[r.neighbors](r.neighbors.md)*,
*[r.univar](r.univar.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
