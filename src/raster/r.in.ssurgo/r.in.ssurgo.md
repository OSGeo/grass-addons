## DESCRIPTION

**r.in.ssurgo** - Import soil data from the USDA NRCS Soil Survey Geographic
Database (SSURGO) into GRASS from either a local copy of the the SSURGO file
geodatabase or from the Soil Data Access (SDA) online API interface. The module
is heavily inspired by the [SoilDB (2.8.9)](https://ncss-tech.github.io/soilDB/index.html)
R package (Beaudette et al., 2025).

The *r.in.ssurgo* imports the Saturated Hydraulic Conductivity of Soils (Ksat) and
the Hydrologic Soil Group (HSG) aggregated for the specified depth range or
master horizon using the the Map Unit Key (mukey) as the spatial unit.
The Ksat values represents the infiltration rateof water through soil when the
soil is 100% saturated are provided. Ksat values are provided in units of cm/hr
and include the low (**ksat_l**), representative (**ksat_r**), and high (**ksat_h**)
estimates of Ksat for each map unit.

The HSG is a soil classification system that groups soils based on their runoff
potential, which is influenced by factors such as texture, structure, and
permeability. The HGS raster (**hydgrp**) are used in rainfall excess models
such as the SCS Curve Number method to estimate runoff from rainfall
events (see *r.curvenumber*).

**ssurgo_areas** is an optional output vector contining the source Multipolygons
and attribute data from the SSURGO Map Unit polygons. This can be used for reference
or to create custom rasters for Curve Number or other applications based on the
SSURGO attributes.

## REQUIREMENTS

[duckdb>=4.1](https://duckdb.org/) Python package for querying and processing data
from the SSURGO file geodatabase.

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
    ssurgo_path="gSSURGO_NC.zip/gSSURGO_NC.gdb" \
    ssurgo_areas="soil_areas" \
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
    ssurgo_path="gSSURGO_NC.zip/gSSURGO_NC.gdb",
    ssurgo_areas="soil_areas",
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
    ssurgo_path="../data/gSSURGO_CONUS.zip/gSSURGO_CONUS.gdb",
    ssurgo_areas="soil_areas",
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

- Beaudette, D., Skovlin, J., Roecker, S., Brown, A. (2025). soilDB
Soil Database Interface. R package version 2.8.9
[https://CRAN.R-project.org/package=soilDB](https://CRAN.R-project.org/package=soilDB)

- Soil Survey Staff, Natural Resources Conservation Service, United States
Department of Agriculture. Web Soil Survey. Available online at
[<https://websoilsurvey.nrcs.usda.gov/>](https://websoilsurvey.nrcs.usda.gov).
Accessed [04/23/2025].

## SEE ALSO

[r.curvenumber](https://grass.osgeo.org/grass-stable/manuals/addons/r.curvenumber.html),
[r.runoff](https://grass.osgeo.org/grass-stable/manuals/addons/r.runoff.html),
[r.sim.water](https://grass.osgeo.org/grass-stable/manuals/addons/r.sim.water.html)

## AUTHORS

Corey T. White

## Sponsors

**r.in.ssurgo** was developed as part of an agreement between the
U.S. Department of Agriculture (USDA), Natural Resources Conservation Service (NRCS)
and North Carolina State University (NCSU) (Recipient), to adapt the SIMulation
of Water and Erosion (SIMWE) model for the integration of Dynamic Soil Survey data.
