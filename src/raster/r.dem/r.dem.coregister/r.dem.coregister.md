## DESCRIPTION

*r.dem.coregister* co-registers a post-event DSM to a reference DEM using
pseudo ground control points (PGCPs) sampled along road centerlines, terrain
assumed stable between surveys. It removes a robust vertical bias and can
optionally chain horizontal (Nuth and Kaab) and ICP refinement.

### method=pgcp_vertical (default)

The **roads** vector is buffered by **buffer** metres and rasterized, the
elevation residual `dem - reference` is sampled within that road mask, and a
robust median vertical bias is estimated. The bias is removed with
`output = dem - median_bias`. Robust statistics (median bias, NMAD, RMSE) are
reported, and with the **-v** flag per-PGCP residuals are written to
**bias_output** as CSV.

If fewer than **min_points** PGCP samples are found the tool warns and proceeds.

### method=nk and method=nk_icp

These chain additional alignment after the PGCP vertical step: `nk` adds a
horizontal and vertical Nuth and Kaab correction (*r.dem.nk*), and `nk_icp`
further adds a point-to-plane ICP refinement (*r.dem.icp*).

## NOTES

The PGCP approach assumes roads are stable reference surfaces. Choose **buffer**
to stay within the paved surface and avoid curbs, vegetation, and vehicles. The
computational region should match the input DEM resolution.

## EXAMPLES

Vertical co-registration from road PGCPs, writing residuals to CSV:

```sh
r.dem.coregister dem=sfm_dsm reference=lidar_dtm roads=road_centerlines \
    output=sfm_dsm_coreg method=pgcp_vertical buffer=2.0 \
    bias_output=pgcp_residuals.csv -v
```

## SEE ALSO

*[r.dem.nk](r.dem.nk.md)*,
*[r.dem.icp](r.dem.icp.md)*,
*[r.dem.change](r.dem.change.md)*,
*[v.buffer](v.buffer.md)*,
*[v.to.rast](v.to.rast.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
