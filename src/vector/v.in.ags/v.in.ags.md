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

### Spatial filtering

The **extent** option accepts a bounding box `xmin,ymin,xmax,ymax` in
geographic degrees (WGS84 / EPSG:4326). This is applied as a server-side
spatial filter before features are downloaded, which can significantly
reduce transfer size for large layers. The relationship between features
and the bounding box is controlled by **spatial_rel** (default:
`esriSpatialRelIntersects`).

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

All data is requested from the server in WGS84 (EPSG:4326) and imported with
*v.import*, which reprojects it into the current project CRS automatically (and
imports directly, without reprojection overhead, when the project is already
WGS84).

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
  extent="-125,42,-116,49"
```

### Change spatial relationship

Import only features **completely within** the bounding box:

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=pnw_states_within \
  extent="-125,42,-116,49" \
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
