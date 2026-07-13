## DESCRIPTION

*v.in.ags* imports vector features from an **ArcGIS Server (AGS) REST API**
feature service or map service layer into a GRASS vector map. The module
constructs the query URL automatically and imports through *v.import*, which
reprojects the data into the current project CRS.

### Download strategy

By default (`download_format=auto`), *v.in.ags* builds the `/query` URL and
hands it to GDAL's **ESRIJSON** driver via *v.import*. GDAL reads the service
directly and scrolls through all pages automatically, so no intermediate file
is written. `download_format=json` is equivalent; `download_format=geojson`
requests GeoJSON and uses GDAL's **GeoJSON** driver instead.

For large layers, `download_format=pbf` enables a fast path that downloads and
decodes **Esri Feature Buffer (PBF)**, a compact binary format, in-process and
writes a temporary GeoJSON file for import. If PBF decoding fails at runtime
the module retries the affected page with GeoJSON automatically.

### Supported service types

Both **FeatureServer** and **MapServer** layer endpoints are supported,
provided the layer exposes the `/query` operation. ArcGIS Server 10.3 or
later is required for pagination; the `pbf` strategy requires ArcGIS Server
10.6 or ArcGIS Online.

### URL formats

The **url** parameter accepts:

- A layer URL ending with a numeric layer index:
  `https://host/arcgis/rest/services/Name/FeatureServer/0`
- A service root URL (without a layer index); in this case use the **layer**
  option to specify which layer to import:
  `https://host/arcgis/rest/services/Name/FeatureServer`

Use the **-l** flag to print all available layers in a service before
importing.

### Inspecting a layer without importing

If **output** is omitted (and **-l** is not used), *v.in.ags* prints
metadata for the resolved layer (id, name, geometry type, feature count,
maximum record count, supported transfer formats, and field names) and
exits without importing anything. This is useful for inspecting a service
before committing to a download.

## NOTES

### Output format

The **format** option controls how text output is printed and applies to
the **-l** layer listing and the layer-inspection mode described above:

- `plain` (default): human-readable text.
- `shell`: shell-script style output (`key=value` for layer info,
  `id|type|name` per line for the layer listing).
- `json`: JSON for downstream parsing.

The **format** option does not affect imports; it is ignored when
**output** is given.

### Attribute filtering

The **where** option accepts any SQL expression supported by the ArcGIS
Server being queried (SQL-92 subset). Examples:

```text
STATE_NAME = 'California'
POP2020 > 100000
TYPE IN ('city', 'town') AND AREA_KM2 < 500
```

### Output extent and spatial filtering

The **extent** option matches *v.import*: `input` (default) imports the full
input, `region` limits the output to the current computational region. With
`extent=region` the region is also converted to a WGS84 bounding box and used
as a server-side filter, so only features overlapping the region are
downloaded.

The **bbox_filter** option accepts an explicit bounding box
`xmin,ymin,xmax,ymax` in geographic degrees (WGS84 / EPSG:4326), applied as a
server-side spatial filter before features are downloaded. This significantly
reduces transfer size for large layers.

**extent** and **bbox_filter** are mutually exclusive. The relationship between
features and the bounding box (either source) is controlled by **spatial_rel**
(default: `esriSpatialRelIntersects`).

### Topology and snapping

Polygon layers served by ArcGIS Server frequently have invalid topology, which
can import with **no areas** (the polygons do not appear). Use **snap** (in map
units of the downloaded data, that is degrees for the default WGS84 download or
**outsr** units otherwise) to snap boundary vertices so areas build. The
default `-1` disables snapping. As with *v.import*, start small (for example
`snap=1e-6`) and increase only if areas are still missing.

### Field selection

Use **fields** to restrict which attribute columns are retrieved. The
default `*` retrieves all fields.

### Result ordering

**order_by** accepts a comma-separated list of field names optionally
followed by `ASC` or `DESC`, for example `STATE_NAME ASC, POP2020 DESC`.

### Geometry options

Use **geometry_precision** to cap the number of coordinate decimal places
returned by the server (reduces transfer size at the cost of spatial
accuracy). Use **max_offset** to request server-side geometry
generalisation; larger values produce fewer vertices.

The **-g** flag skips geometry entirely and imports the attribute table
only.

### Pagination

Pagination is automatic. In the default strategy GDAL scrolls through all
pages of the service. In the `pbf` strategy *v.in.ags* reads `maxRecordCount`
from the service metadata and issues successive
`resultOffset`/`resultRecordCount` requests until all matching features have
been retrieved; if that service reports `supportsPagination: false`, a warning
is issued and only the first page is imported.

### Coordinate reference system

By default data is requested from the server in WGS84 (EPSG:4326) and imported
with *v.import*, which reprojects it into the current project CRS automatically
(and imports directly, without reprojection overhead, when the project is
already WGS84).

Use **outsr** to request a different output spatial reference (an ArcGIS
`outSR` WKID, for example `3358`). Setting **outsr** to the project's WKID makes
the server do the reprojection, so *v.import* imports directly with no
client-side transform. The final map is always in the project CRS regardless.
**outsr** is ignored by the `pbf` strategy, which always uses EPSG:4326.

As in *v.import*, **datum_trans** selects the datum transform used during
reprojection (`-1` lists the available transforms), and the **-o** flag
overrides the projection check, assuming the downloaded data already has the
project's CRS (pairs well with `outsr=<project WKID>`).

### Temporary files

Only the `pbf` strategy writes a temporary GeoJSON file (in the system
temporary directory, removed automatically on exit). The default strategy
streams the service through GDAL and creates no temporary file.

## EXAMPLES

### List layers available in a service

```sh
v.in.ags -l url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer
```

### Import all features

Data is reprojected into the current project CRS automatically:

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=usa_states
```

### Import with an attribute filter

Import only Californian counties:

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Counties_Generalized/FeatureServer/0 \
  output=california_counties \
  where="STATE_NAME = 'California'"
```

### Import with a spatial bounding-box filter

Import features intersecting a bounding box over the US Pacific Northwest
(WGS84 coordinates):

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=pnw_states \
  bbox_filter="-125,42,-116,49"
```

### Limit the import to the current region

`extent=region` filters on the server by the current region and clips the
output to it:

```sh
g.region n=49 s=42 w=-125 e=-116
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=pnw_states \
  extent=region
```

### Fix polygon topology with snapping

If imported polygons show no areas, snap boundary vertices:

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=usa_states \
  snap=1e-6
```

### Change spatial relationship

Import only features **completely within** the bounding box:

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=pnw_states_within \
  bbox_filter="-125,42,-116,49" \
  spatial_rel=esriSpatialRelWithin
```

### Import with reduced precision and simplified geometry

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Counties_Generalized/FeatureServer/0 \
  output=counties_simplified \
  geometry_precision=4 \
  max_offset=0.001
```

### Import selected fields in a sorted order

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=usa_states_slim \
  fields="STATE_NAME,STATE_ABBR,POP2020" \
  order_by="POP2020 DESC"
```

### Request data already in the project CRS

Ask the server for the project's spatial reference (here NC State Plane,
EPSG:3358) so no client-side reprojection is needed:

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=usa_states \
  outsr=3358
```

### Use the PBF fast path for a large layer

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Counties_Generalized/FeatureServer/0 \
  output=usa_counties \
  download_format=pbf
```

### Inspect a layer as JSON without importing

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  format=json
```

### Import attribute table only (no geometry)

```sh
v.in.ags -g \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=usa_state_attrs
```

### Python scripting example

```python
import grass.script as gs

gs.run_command(
    "v.in.ags",
    url="https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0",
    output="usa_states",
    where="POP2020 > 1000000",
    fields="STATE_NAME,STATE_ABBR,POP2020",
    order_by="POP2020 DESC",
    download_format="auto",
    overwrite=True,
)
```

## REFERENCES

- [ArcGIS REST API – Query (Feature Service)](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm)
- [ArcGIS REST API – Query (Map Service)](https://developers.arcgis.com/rest/services-reference/enterprise/query-map-service-layer-.htm)
- [Esri Feature Buffer (PBF) specification](https://github.com/Esri/arcgis-pbf)
- [OGR GeoJSON driver](https://gdal.org/drivers/vector/geojson.html)
- [OGR ESRI JSON driver](https://gdal.org/drivers/vector/esrijson.html)
- [RFC 7946 – The GeoJSON Format](https://www.rfc-editor.org/rfc/rfc7946)

## SEE ALSO

*[v.import](v.import.md),
[v.in.ogr](v.in.ogr.md),
[v.in.wfs](v.in.wfs.md),
[v.proj](v.proj.md)*

## AUTHORS

Corey T. White [NCSU GeoForAll Lab](https://geospatial.ncsu.edu/geoforall/)
