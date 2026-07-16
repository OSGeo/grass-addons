## DESCRIPTION

**r.in.ssurgo** - Import soil data from the USDA NRCS Soil Survey Geographic
Database (SSURGO) into GRASS from either a local copy of the the SSURGO file
geodatabase or from the Soil Data Access (SDA) online API interface. The module
is heavily inspired by the [SoilDB (2.8.9)](https://ncss-tech.github.io/soilDB/index.html)
R package (Beaudette et al., 2025).

The tool will either use the SDA API to query and download data for the current
computational region or read from a local copy of the SSURGO file geodatabase.
The SDA API is used unless a local path to the SSURGO file geodatabase
is provided to `ssurgo_path`. The SSURGO data can be downloaded from USDA
NRCS at the following links:

* [SSURGO CONUS](https://nrcs.app.box.com/v/soils/folder/233395259341)
* [SSURGO by State](https://nrcs.app.box.com/v/soils/folder/233398887779)

The downloaded gSSURGO files can be used directly without unzipping
the file geodatabase. *r.in.ssurgo* can read the zipped
file geodatabase directly using GDAL's virtual file system.

```bash
ssurgo_path="path/to/gSSURGO_NC.zip"
```

However, you may also pass the path to an unzipped file geodatabase if you prefer.

```bash
ssurgo_path="path/to/gSSURGO_NC/gSSURGO_NC.gdb"
```

## NOTES

The Saturated Hydraulic Conductivity (Ksat) and the Hydrologic Soil Group
(HSG) are aggregated for the specified depth range or master horizon using the
Map Unit Key (mukey) as the spatial unit. Ksat is the rate at which water
moves vertically through saturated soil; values are provided in **mm/hr**
(SSURGO stores them as µm/s and the module multiplies by 3.6) and include
the low (**ksat_l**), representative (**ksat_r**), and high (**ksat_h**)
estimates per map unit.

The HSG is a soil classification system that groups soils based on their runoff
potential, which is influenced by factors such as texture, structure, and
permeability. The HGS raster (**hydgrp**) are used in rainfall excess models
such as the SCS Curve Number method to estimate runoff from rainfall
events (see *r.curvenumber*).

The soil texture separates (**sand**, **silt**, **clay**, in percent) and the
bulk density at 1/3 bar (**bulk_density**, g/cm3) can also be written as
rasters, aggregated the same way as Ksat. These match the inputs of the ROSETTA
pedotransfer model, so they can be passed directly to *r.soils.rosetta* to
estimate van Genuchten soil hydraulic parameters.

The **soils** output is a vector layer containing the source SSURGO Map Unit polygons
and attribute data. This can be used for reference or to create custom rasters for
Curve Number or other applications based on the SSURGO attributes.

### Attributes on the **soils** vector

In addition to **mukey** / **mukey_int**, the soils vector carries the
following dominant-component and depth-weighted attributes for the requested
[hzdept_r, hzdepb_r] range and master horizon designation. Use them with
`v.to.rast use=attr attribute_column=<field>` to derive any of these as
rasters on demand.

| Field | Type | Description |
| ------ | ------ | ------ |
| `cokey` | TEXT | Component key of the dominant component |
| `comppct_r` | REAL | Dominant component's percentage of the map unit |
| `hydgrp` | TEXT | Hydrologic Soil Group (A, B, C, D, A/D, …) |
| `compname` | TEXT | Component name |
| `drainagecl` | TEXT | Drainage class |
| `slope_r` | REAL | Component slope (%) |
| `ksat_l` | REAL | Saturated hydraulic conductivity, low (mm/hr) |
| `ksat_r` | REAL | Saturated hydraulic conductivity, representative (mm/hr) |
| `ksat_h` | REAL | Saturated hydraulic conductivity, high (mm/hr) |
| `sandtotal_r` | REAL | Sand content (%) |
| `silttotal_r` | REAL | Silt content (%) |
| `claytotal_r` | REAL | Clay content (%) |
| `awc_r` | REAL | Available water capacity (cm/cm) |
| `om_r` | REAL | Organic matter (%) |
| `dbthirdbar_r` | REAL | Bulk density at 1/3 bar (g/cm³) |
| `ph1to1h2o_r` | REAL | Soil reaction (pH 1:1 H₂O) |
| `cec7_r` | REAL | Cation exchange capacity at pH 7 (meq/100 g) |

Depth-weighted REAL fields are aggregated as
`SUM(thk × value) / SUM(thk)` over horizons that overlap the requested
depth range, where `thk` is each horizon's thickness clipped to that range.

### Filtering by Depth or Master Horizon

The user can specify a depth range [cm] (top and bottom) or a master horizon
designation (`desgnmaster`). The master horizon is the most representative horizon
of a soil profile and is designated by a capital letter (A, E, B, C, R) in the
SSURGO database. If a master horizon is specified, the Ksat and HSG values will
be based on the specified master horizon. If a depth range is specified, the
Ksat and HSG values will be aggregated for the specified depth range.

### Aggregation Methods

Soils are aggregated using either the dominant component or a weighted average
of all components in the map unit, depending on the specified depth range or
master horizon.

### r3 (3D raster) output for depth profiles

When `depths` is set (a comma-separated, strictly-increasing list of cm
boundaries with at least 2 values), the depth-weighted outputs
(**ksat_l**, **ksat_r**, **ksat_h**, **sand**, **silt**, **clay**,
**bulk_density**) are produced as **3D rasters** with
one z-slice per depth bin instead of a single 2D average. The number of
slices is `len(depths) - 1`. `hzdept_r` and `hzdepb_r` are ignored when
`depths` is set; the aggregation runs once per slice.

`hydgrp` and `mukey` always remain 2D — they're profile-level / identity
values, not depth-dependent.

The 3D region is set with `b=0`, `t=max(depths)` so the z-axis represents
depth (cm) from the surface; slice 0 is at z=0 to z=depths[1], slice
N-1 is at z=depths[-2] to z=depths[-1]. Adjust with `g.region -3` if you
prefer a different convention.

```sh
r.in.ssurgo \
    ssurgo_path="gSSURGO_NC.zip" \
    soils="soil_areas" \
    hydgrp="hydgrp" \
    ksat_r="ksat_r" \
    depths="0,15,30,60,100" \
    desgnmaster="A"
# produces: hydgrp (2D), ksat_r (3D, 4 slices)
```

```python
tools.r_in_ssurgo(
    ssurgo_path="../data/gSSURGO_CONUS.zip",
    soils="soil_areas",
    ksat_r="ksat_r",
    depths="0,15,30,60,100",
    desgnmaster="A",
)
```

The intermediate per-slice columns (`ksat_r__s0`, `ksat_r__s1`, …) also
appear on the **soils** vector if you want to access them as 2D rasters
or query them via `v.db.select`.

### Choosing the local-import backend

When importing from a local SSURGO file geodatabase, *r.in.ssurgo* uses the
[DuckDB](https://duckdb.org/) Python package by default if it is installed.
If DuckDB is unavailable, the tool falls back to a pure GDAL/OGR + SQLite
implementation that uses GRASS's bundled attribute database. The `-s` flag
forces the SQLite/OGR backend even when DuckDB is importable, which is
useful for testing the fallback path or running on environments where DuckDB
should be avoided. The flag has no effect on Soil Data Access (SDA) queries
(used when `ssurgo_path` is not set).

### SSURGO Download

* [SSURGO CONUS](https://nrcs.app.box.com/v/soils/folder/233395259341)
* [SSURGO by State](https://nrcs.app.box.com/v/soils/folder/233398887779)

> If you choose to use the downloaded dataset instead of the SDA API you do
> not need to unzip the folder. `r.in.ssurgo` expects the data to be zipped.

## REQUIREMENTS

[duckdb>=1.4.4](https://duckdb.org/) Python package for querying and processing
data from the SSURGO file geodatabase.

```sh
pip install duckdb
```

[GDAL>=3.1](https://gdal.org/) for reading and writing geospatial data formats.
DuckDB uses [FlatGeobuf](https://flatgeobuf.org/) for spatial data, which is
supported in GDAL 3.1 and later.

## EXAMPLES

Import Ksat data for the current region from a local copy of the SSURGO file geodatabase:

=== Command line

```sh
r.in.ssurgo \
    ssurgo_path="gSSURGO_NC.zip" \
    soils="soil_areas" \
    hydgrp="hydgrp" \
    ksat_l="ksat_l" \
    ksat_r="ksat_r" \
    ksat_h="ksat_h" \
    mukey="mukey" \
    hzdept_r=0 \
    hzdepb_r=100 \
    desgnmaster="A"
```

=== Python (grass.script)

```python
gs.run_command(
    "r.in.ssurgo",
    ssurgo_path="gSSURGO_NC.zip",
    soils="soils",
    hydgrp="hydgrp",
    ksat_l="ksat_l",
    ksat_r="ksat_r",
    ksat_h="ksat_h",
    mukey="mukey",
    hzdept_r=0,
    hzdepb_r=100,
    desgnmaster="A",
)
```

=== Python (grass.tools)

```python
tools = Tools()
tools.r_in_ssurgo(
    ssurgo_path="../data/gSSURGO_CONUS.zip",
    soils="soils",
    hydgrp="hydgrp",
    ksat_l="ksat_l",
    ksat_r="ksat_r",
    ksat_h="ksat_h",
    mukey="mukey",
    hzdept_r=0,
    hzdepb_r=100,
    desgnmaster="A",
)
```

Import soil texture and bulk density for the top 25.4 cm and estimate van
Genuchten hydraulic parameters with *r.soils.rosetta* (see its manual for the
full SSURGO-to-SIMWE workflow):

```sh
r.in.ssurgo \
    ssurgo_path="gSSURGO_NC.zip" \
    soils="soils" \
    sand="sand" \
    silt="silt" \
    clay="clay" \
    bulk_density="bd" \
    hzdept_r=0 \
    hzdepb_r=25.4
r.soils.rosetta sand="sand" silt="silt" clay="clay" bulk_density="bd" \
    ksat="ksat_vg" version=3
```

Force the SQLite/OGR backend (skip DuckDB) for a local import:

```sh
r.in.ssurgo -s \
    ssurgo_path="gSSURGO_NC.zip" \
    soils="soils" \
    hydgrp="hydgrp" \
    ksat_r="ksat_r" \
    hzdept_r=0 \
    hzdepb_r=100 \
    desgnmaster="A"
```

```python
tools.r_in_ssurgo(
    ssurgo_path="../data/gSSURGO_CONUS.zip",
    soils="soils",
    hydgrp="hydgrp",
    ksat_r="ksat_r",
    hzdept_r=0,
    hzdepb_r=100,
    desgnmaster="A",
    flags="s",
)
```

=== Command line

```sh
r.in.ssurgo \
    soils="soils" \
    hydgrp="hydgrp" \
    ksat_l="ksat_l" \
    ksat_r="ksat_r" \
    ksat_h="ksat_h" \
    mukey="mukey" \
    hzdept_r=0 \
    hzdepb_r=100 \
    desgnmaster="A"
```

Import hydrologic soil group (HSG) data for the current region from the Soil
Data Access (SDA) online API interface:

=== Python (grass.script)

```python
gs.run_command(
    "r.in.ssurgo",
    soils="soils",
    hydgrp="hydgrp",
    ksat_l="ksat_l",
    ksat_r="ksat_r",
    ksat_h="ksat_h",
    mukey="mukey",
    hzdept_r=0,
    hzdepb_r=100,
    desgnmaster="A",
)
```

=== Python (grass.tools)

```python
tools = Tools()
tools.r_in_ssurgo(
    soils="soils",
    hydgrp="hydgrp",
    ksat_l="ksat_l",
    ksat_r="ksat_r",
    ksat_h="ksat_h",
    mukey="mukey",
    hzdept_r=0,
    hzdepb_r=100,
    desgnmaster="A",
)
```

## REFERENCES

* Beaudette, D., Skovlin, J., Roecker, S., Brown, A. (2025). soilDB
Soil Database Interface. R package version 2.8.9
[https://CRAN.R-project.org/package=soilDB](https://CRAN.R-project.org/package=soilDB)

* Soil Survey Staff, Natural Resources Conservation Service, United States
Department of Agriculture. Web Soil Survey. Available online at
[<https://websoilsurvey.nrcs.usda.gov/>](https://websoilsurvey.nrcs.usda.gov).
Accessed [04/23/2025].

## SEE ALSO

[r.curvenumber](https://grass.osgeo.org/grass-stable/manuals/addons/r.curvenumber.html),
[r.runoff](https://grass.osgeo.org/grass-stable/manuals/addons/r.runoff.html),
[r.sim.water](https://grass.osgeo.org/grass-stable/manuals/addons/r.sim.water.html),
[r.soils.rosetta](https://grass.osgeo.org/grass-stable/manuals/addons/r.soils.rosetta.html)

## AUTHORS

Corey T. White

## Sponsors

**r.in.ssurgo** was developed as part of an agreement between the
U.S. Department of Agriculture (USDA), Natural Resources Conservation Service (NRCS)
and North Carolina State University (NCSU) (Recipient), to adapt the SIMulation
of Water and Erosion (SIMWE) model for the integration of Dynamic Soil Survey data.
