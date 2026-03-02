## DESCRIPTION

*v.in.ags* imports vector features from an **ArcGIS Server (AGS) REST API**
feature service or map service layer into a GRASS vector map. The module
constructs query URLs automatically, handles server-side pagination
transparently, and delegates the final import to *v.in.ogr* (default) or
*v.import* (with the **-r** flag for on-the-fly reprojection).

Geometry is always requested from the server in WGS84 (EPSG:4326) so that
the intermediate GeoJSON file is standards-compliant (RFC 7946). When the
current GRASS project is not in WGS84, use **-r** to reproject the data
during import.

### Supported service types

Both **FeatureServer** and **MapServer** layer endpoints are supported,
provided the layer exposes the `/query` operation and supports GeoJSON output
(`f=geojson`). ArcGIS Server 10.3 or later is required for pagination support;
on older servers only the first page of results (up to `maxRecordCount`) is
downloaded.

### URL formats

The **url** parameter accepts:

- A layer URL ending with a numeric layer index:
  `https://host/arcgis/rest/services/Name/FeatureServer/0`
- A service root URL (without a layer index); in this case use the **layer**
  option to specify which layer to import:
  `https://host/arcgis/rest/services/Name/FeatureServer`

Use the **-l** flag to print all available layers in a service before
importing.

## NOTES

### Attribute filtering

The **where** option accepts any SQL expression supported by the ArcGIS Server
being queried (standard SQL-92 subset). Examples:

```text
STATE_NAME = 'California'
POP2020 > 100000
TYPE IN ('city', 'town') AND AREA_KM2 < 500
```

### Spatial filtering

The **extent** option accepts a bounding box
`xmin,ymin,xmax,ymax` in geographic degrees (WGS84 / EPSG:4326).
This is applied as an intersects filter on the server side before features
are downloaded, which can significantly reduce transfer size for large layers.

### Field selection

Use **fields** to restrict which attribute columns are retrieved. This reduces
download size when only a subset of attributes is needed. The default `*`
retrieves all fields.

### Pagination

*v.in.ags* queries the service metadata to obtain `maxRecordCount` and then
issues successive requests using `resultOffset`/`resultRecordCount` until all
matching features have been retrieved. No manual batching is required.

If the service reports `supportsPagination: false`, a warning is issued and
only the first page of results is imported.

### Coordinate reference system

All data is downloaded in WGS84. When using the default *v.in.ogr* import
the output map will be in WGS84; ensure your project is in WGS84 or use
**-r** so that *v.import* reprojects the data automatically.

### Temporary files

A temporary GeoJSON file is created in the system temporary directory during
import and removed automatically on exit.

## EXAMPLES

### List layers available in a service

```sh
v.in.ags -l url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer
```

### Import all features from a FeatureServer layer

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=usa_states
```

### Import with attribute filter and reprojection

Import only Californian counties, reprojecting to the current project CRS:

```sh
v.in.ags -r \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Counties_Generalized/FeatureServer/0 \
  output=california_counties \
  where="STATE_NAME = 'California'"
```

### Import with a spatial bounding-box filter

Import features intersecting a bounding box over the US Pacific Northwest
(WGS84 coordinates):

```sh
v.in.ags -r \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=pnw_states \
  extent="-125,42,-116,49"
```

### Import selected fields only

```sh
v.in.ags \
  url=https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0 \
  output=usa_states_simple \
  fields="STATE_NAME,STATE_ABBR,POP2020"
```

### Import from a MapServer layer using the service root URL

```sh
v.in.ags \
  url=https://sampleserver6.arcgisonline.com/arcgis/rest/services/USA/MapServer \
  layer=2 \
  output=usa_highways
```

### Python scripting example

```python
import grass.script as gs

gs.run_command(
    "v.in.ags",
    flags="r",
    url="https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0",
    output="usa_states",
    where="POP2020 > 1000000",
    overwrite=True,
)
```

## REFERENCES

- [ArcGIS REST API – Query (Feature Service)](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm)
- [ArcGIS REST API – Query (Map Service)](https://developers.arcgis.com/rest/services-reference/enterprise/query-map-service-layer-.htm)
- [OGR GeoJSON driver](https://gdal.org/drivers/vector/geojson.html)
- [RFC 7946 – The GeoJSON Format](https://www.rfc-editor.org/rfc/rfc7946)

## SEE ALSO

*[v.import](v.import.md),
[v.in.ogr](v.in.ogr.md),
[v.in.wfs](v.in.wfs.md),
[v.proj](v.proj.md)*

## AUTHORS

Corey White
