## DESCRIPTION

*r.noaa.atlas14* downloads and imports NOAA Atlas 14 precipitation-frequency
data into GRASS. It supports two acquisition modes:

- **mode=point** queries the NOAA Precipitation Frequency Data Server (PFDS)
  point-query endpoint for a single longitude/latitude and writes the returned
  precipitation-frequency estimates as JSON or CSV. Optionally, a GRASS vector
  point map is created with the expected/upper/lower tables stored as JSON
  attributes.
- **mode=grid** discovers, downloads, and imports NOAA Atlas 14 GIS-compatible
  grid archives (ZIP) for a given Atlas 14 volume/subregion, optionally filtered
  by duration, average recurrence interval (ARI), bound, statistic, units, and
  series. A manifest CSV describing the imported rasters can be written.

The module retrieves data directly from NOAA's public services:

- PFDS point query: `https://hdsc.nws.noaa.gov/cgi-bin/new/fe_text.csv`
- GIS grid archives: `https://hdsc.nws.noaa.gov/pub/hdsc/data/` (autodiscovery),
  or any user-supplied `archive_url=`.

## NOTES

### Point mode

Point results include the *expected* value and the *upper*/*lower* bounds of
the 90% confidence interval, for each duration/return-period combination
published by NOAA. Use `bound=expected|upper|lower|all` to select the table(s).

`coordinates=` accepts one or more `lon,lat` pairs, e.g.
`coordinates=-78.6382,35.7796,-81.0,29.5`. When `coordinates=` is omitted,
the module queries the center of the current computational region; the
region bounds are reprojected to WGS84 lon/lat via `g.region -b` so this
works from any GRASS location CRS.

When multiple points are queried, JSON output is emitted as a list of
per-point result objects, and CSV output prepends `lon,lat,bound` columns so
rows from different points and bounds can be disambiguated. Single-point
output keeps the original unwrapped format for backward compatibility.

The `statistic` option controls whether PFDS returns precipitation *depth* or
*intensity*. The `units` option (`english` or `metric`) and `series` option
(`pds` or `ams` — partial-duration or annual-maximum series) are passed
through to PFDS.

If `vector_output=` is given, the module creates a one-point vector map with
columns `lon`, `lat`, `expected_json`, `upper_json`, `lower_json`. The JSON
columns contain the full per-duration tables so they can be queried later with
`v.db.select` / `db.select`.

### Grid mode

Grid autodiscovery parses the HTTPS directory listing at `base_gis_url=` and
filters by a region code (`region=`), e.g. `se` for Volume 9 Southeastern
States. Filenames are parsed heuristically to extract bound, statistic, units,
series, duration, and ARI; these are then matched against the user-supplied
filters.

Because NOAA naming conventions vary across volumes, autodiscovery may miss
some archives. In that case, pass `archive_url=` directly with either a ZIP
URL or a directory listing URL that contains the ZIPs.

The `-l` flag lists matching archives (as JSON lines) without downloading them.

Filtering behavior:

- `durations=` and `aris=` are *strict*: candidates whose duration or ARI
  could not be inferred from the filename are rejected.
- `bound=`, `statistic=`, `units=`, `series=` are *permissive*: a candidate
  with an unknown attribute is allowed through, to avoid discarding rasters
  whose filenames don't encode every attribute.

Rasters are imported with `r.in.gdal` by default; pass `-i` to use `r.import`
(which supports reprojection via `resample=`). Pass `-o` to override the
projection check when using `r.in.gdal`. Imported raster names follow the
pattern `<output_prefix>_<statistic>_<bound>_<duration>_<ari>yr_<units>_<series>_<region>`,
with missing parts omitted.

### Safety

Extracted ZIP members are validated against path traversal (zip-slip): any
member whose resolved path escapes the temporary extraction directory causes
the import to abort.

## EXAMPLES

### Point query to CSV

```sh
r.noaa.atlas14 mode=point coordinates=-78.6382,35.7796 \
    statistic=intensity units=english series=pds bound=expected \
    format=csv output=/tmp/raleigh_idf.csv
```

### Point query to JSON and create a vector point

```sh
r.noaa.atlas14 mode=point coordinates=-78.6382,35.7796 \
    statistic=depth units=english series=pds bound=all \
    format=json output=/tmp/raleigh_atlas14.json \
    vector_output=atlas14_raleigh
```

### Multiple points as a single CSV and a multi-point vector

```sh
r.noaa.atlas14 mode=point \
    coordinates=-78.6382,35.7796,-80.8431,35.2271,-77.8868,34.2257 \
    statistic=depth units=english series=pds bound=expected \
    format=csv output=/tmp/nc_cities_idf.csv \
    vector_output=atlas14_nc_cities
```

### Query the center of the current computational region

```sh
g.region raster=elevation
r.noaa.atlas14 mode=point format=json bound=expected
```

### List matching grid archives without importing

```sh
r.noaa.atlas14 mode=grid region=se -l
```

### Import a known archive directly

```sh
r.noaa.atlas14 mode=grid archive_url="https://hdsc.nws.noaa.gov/pub/hdsc/data/se/se_100yr_24hr.zip" \
    output_prefix=a14 -i
```

### Import filtered subset and write a manifest

```sh
r.noaa.atlas14 mode=grid region=se \
    durations=24hr,2day aris=10,100 bound=expected \
    output_prefix=a14 output=/tmp/a14_manifest.csv -i
```

## REFERENCES

- Bonnin, G. M., D. Martin, B. Lin, T. Parzybok, M. Yekta, and D. Riley (2004–2019),
  NOAA Atlas 14: Precipitation-Frequency Atlas of the United States.
  NOAA, National Weather Service, Silver Spring, Maryland.
- NOAA Precipitation Frequency Data Server (PFDS):
  [https://hdsc.nws.noaa.gov/pfds/](https://hdsc.nws.noaa.gov/pfds/)

## SEE ALSO

- *[r.in.gdal](https://grass.osgeo.org/grass-stable/manuals/r.in.gdal.html)*,
- *[r.import](https://grass.osgeo.org/grass-stable/manuals/r.import.html)*,
- *[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html)*,
- *[r.sim.water](https://grass.osgeo.org/grass-stable/manuals/r.sim.water.html)*

## AUTHORS

Corey T. White, [OpenPlains Inc.](https://openplains.com) &amp; Center for
Geospatial Analytics, North Carolina State University
