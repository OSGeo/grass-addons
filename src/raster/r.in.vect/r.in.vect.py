#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.in.vect
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Convert an external vector layer to a raster layer
#               using gdal.Rasterize, and imports the resulting raster in GRASS GIS
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Converts an external vector layer to a raster layer using gdal.Rasterize and imports this raster layer.
# % keyword: vector
# % keyword: raster
# % keyword: import
# % keyword: convert
# % keyword: heatmap
# %end

# %option G_OPT_F_BIN_INPUT
# %end

# %option
# % key: layer
# % label: OGR layer name
# % description: OGR layer name, like the name of an shapefile  or the name of a layer in a Geopackage (see v.in.ogr for examples)
# % guisection: Input
# %end

# %option G_OPT_R_OUTPUT
# % required: yes
# %end

# %option G_OPT_DB_COLUMN
# % key: attribute_column
# % label: Column with raster values
# % description: Name of attribute column that hold the values to be used as raster values (data type must be numeric)
# % guisection: Raster values
# %end

# %option G_OPT_DB_COLUMN
# % key: label_column
# % label: Column with raster labels
# % description: Name of attribute column that hold the values to be used as raster labels
# % guisection: Raster values
# %end

# %option
# % key: value
# % type: integer
# % label: Raster value
# % description: Raster value (if attribute_column is left empty)
# % guisection: Raster values
# %end

# %flag
# % key: c
# % label: Count overlapping features
# % description: Count overlapping features (additive mode). Sets burn value to 1, sums overlaps, and initializes raster to 0.
# % guisection: Raster values
# %end

# %option
# % key: background
# % type: double
# % label: Value for background pixels
# % description: Value to assign to pixels not covered by features. If not given, these pixels will be set to NULL (nodata).
# % guisection: Raster values
# % required: no
# %end

# %option G_OPT_DB_WHERE
# % description: Attribute query for selecting features (without the WHERE keyword), e.g. "type = 'road' AND status = 1". Mutually exclusive with 'sql'.
# % guisection: Selection
# % required: no
# %end

# %option
# % key: sql
# % type: string
# % label: SQL statement
# % description: SQL statement to select or alter features. Mutually exclusive with 'where'.
# % guisection: Selection
# % required: no
# %end

# %flag
# % key: v
# % label: Convert whole vector
# % description: Set this flag if the whole vector layer needs to be converted. By default, only the part overlapping with the computational region is converted.
# %end

# %flag
# % key: r
# % label: Match region to vector bounding box
# % description: Set region extent to match that of the bounding box of the vector layer.
# %end

# %flag
# % key: d
# % label: Create densified lines
# % description: Pixels touched by lines or polygons will be included, not just those on the line render path, or whose center point is within the polygon  (default: thin lines).
# %end

# %flag
# % key: l
# % label: Linearize curved geometries
# % description: Convert curved geometry types (e.g., MultiSurface, CurvePolygon) to their linear equivalents before rasterizing. Required for sources like the Dutch BGT that use curve-based GML geometries.
# %end

# %flag
# % key: a
# % label: Print attribute table columns
# % description: Print the names of the columns in the attribute table and exit
# %end

# %option G_OPT_MEMORYMB
# %end

# %rules
# % requires_all: -r,-v
# %end

# %rules
# % required: value,attribute_column,-c,-a
# %end

# %rules
# % exclusive: value,attribute_column,-c,-a
# %end

# %rules
# % exclusive: where,sql
# %end

# Libraries
import atexit
import os
import sys
import numpy as np
import grass.script as gs

clean_maps = []
_temp_region_used = False


def cleanup():
    """Remove temporary files specified in the global list (and delete temp region if used)."""
    global _temp_region_used

    for path in clean_maps:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except Exception as e:
            gs.warning(_("Unable to delete temporary file {}: {}").format(path, e))

    # ensure temp region is deleted if one is created created
    if _temp_region_used:
        try:
            gs.del_temp_region()
        except Exception as e:
            gs.warning(_("Unable to delete temporary region: {}").format(e))


def get_grass_crs_wkt():
    """Get the CRS of the computational region"""

    projection_info = gs.read_command("g.proj", flags="wf")
    return projection_info.rstrip()


def get_vector_crs_wkt(vector_file, layer_name=None):
    """Get CRS (WKT) of selected vector layer)"""
    vector = ogr.Open(vector_file)
    if vector is None:
        gs.fatal(_("Could not open {}").format(vector_file))

    if layer_name:
        layer = vector.GetLayerByName(layer_name)
        if layer is None:
            vector = None
            gs.fatal(_("Layer {} not found in {}").format(layer_name, vector_file))
    else:
        layer = vector.GetLayer(0)

    spatialRef = layer.GetSpatialRef()
    if not spatialRef:
        vector = None
        gs.fatal(_("Layer does not have a spatial reference"))

    wkt = spatialRef.ExportToWkt()
    vector = None
    return wkt


def check_wkt_match(grass_wkt, vector_wkt):
    """
    Compare the CRS of the vector layer with the CRS of the GRASS region.
    Uses traditional GIS axis order to avoid false mismatches due to axis mapping.
    """
    # Create spatial reference objects
    grass_srs = osr.SpatialReference()
    grass_srs.ImportFromWkt(grass_wkt)

    given_srs = osr.SpatialReference()
    given_srs.ImportFromWkt(vector_wkt)

    # Axis-order safety (GDAL/PROJ 6+): standardize mapping before comparison
    try:
        grass_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        given_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    except Exception:
        # If not available (older GDAL), fall back to default behavior
        pass

    return grass_srs.IsSame(given_srs) == 1


def get_data_type(vector_file, layer_name, column_name, sql=None):
    """Get the data type of the selected column"""
    # Open the vector file
    datasource = ogr.Open(vector_file, 0)
    if datasource is None:
        raise FileNotFoundError(f"Could not open {vector_file}")

    layer = None
    if sql:
        # If SQL is provided, execute it to get the resulting layer definition
        layer = datasource.ExecuteSQL(sql, dialect="SQLITE")
        if layer is None:
            datasource = None
            raise ValueError(f"SQL statement returned no results or is invalid: {sql}")
    else:
        # Get the specified layer
        if layer_name:
            layer = datasource.GetLayerByName(layer_name)
            if layer is None:
                datasource = None
                raise ValueError(f"Layer {layer_name} not found in {vector_file}")
        else:
            layer = datasource.GetLayer(0)

    # Get the layer's schema (field definitions)
    layer_definition = layer.GetLayerDefn()
    field_count = layer_definition.GetFieldCount()

    # Find the specified column
    field_type_name = None
    for i in range(field_count):
        field_definition = layer_definition.GetFieldDefn(i)
        if field_definition.GetName() == column_name:
            field_type = field_definition.GetType()
            field_type_name = field_definition.GetFieldTypeName(field_type)

    if sql:
        datasource.ReleaseResultSet(layer)
    datasource = None

    if field_type_name is None:
        raise ValueError(
            f"Column {column_name} not found in attribute table of {vector_file}"
        )

    return field_type_name


def raster_labels(vector_file, layer_name, raster, column_name, column_rat, where=None):
    """Add labels to raster layer"""
    datasource = ogr.Open(vector_file)
    if datasource is None:
        raise FileNotFoundError(f"Could not open {vector_file}")

    # Use SQL to fetch only unique id/label pairs instead of iterating all features
    table = layer_name if layer_name else datasource.GetLayer(0).GetName()
    sql = (
        f'SELECT DISTINCT "{column_name}", "{column_rat}" '
        f'FROM "{table}" '
        f'WHERE "{column_name}" IS NOT NULL AND "{column_rat}" IS NOT NULL'
    )
    if where:
        sql += f" AND ({where})"

    layer = datasource.ExecuteSQL(sql, dialect="SQLITE")
    if layer is None:
        datasource = None
        raise ValueError("SQL query for raster labels returned no results")

    ids = []
    labels = []

    for feature in layer:
        ids.append(feature.GetField(0))
        labels.append(feature.GetField(1))

    datasource.ReleaseResultSet(layer)
    datasource = None

    # Print warning if number of unique ids do not match number of unique labels
    if len(np.unique(ids)) < len(np.unique(labels)):
        gs.warning(
            _(
                "The number of unique raster values (based on column '{0}') is smaller "
                "than the number of unique labels in the column '{1}'. This means "
                "that there are raster value with more than one matching label."
                "For those raster values, the first label in column '{1}' is used."
            ).format(column_name, column_rat)
        )

    # Create category rules: first label per id wins
    unique_ids = {}
    for i in range(len(ids)):
        if ids[i] not in unique_ids:
            unique_ids[ids[i]] = labels[i]

    cat_rules = "\n".join([f"{k}|{v}" for k, v in unique_ids.items()])

    gs.write_command(
        "r.category", map=raster, rules="-", stdin=cat_rules, separator="pipe"
    )


def main(options, flags):
    global _temp_region_used
    try:
        from osgeo import ogr, gdal, osr  # noqa: E402
    except ModuleNotFoundError:
        gs.fatal(_("GDAL Python package is not installed."))

    ogr.UseExceptions()

    # Get variables
    vector_file = options["input"]
    vector_layer = options["layer"] or None
    where = options.get("where") or None
    sql = options.get("sql") or None
    count_mode = flags["c"]

    # Check if there are multiple layers and none specified (only if SQL is not used)
    if vector_layer is None and not sql:
        ds = ogr.Open(vector_file)
        if ds is None:
            gs.fatal(_("Could not open input file '{}'").format(vector_file))

        if ds.GetLayerCount() > 1:
            layers = [ds.GetLayer(i).GetName() for i in range(ds.GetLayerCount())]
            ds = None
            gs.fatal(
                _(
                    "Input file contains more than one layer. Please use the 'layer' "
                    "option to select one.\nAvailable layers: {}"
                ).format(", ".join(layers))
            )
        ds = None

    # Handle printing columns (Exit if flag 'a' is set)
    if flags["a"]:
        ds = ogr.Open(vector_file)
        if ds is None:
            gs.fatal(_("Could not open input file '{}'").format(vector_file))

        if sql:
            layer = ds.ExecuteSQL(sql, dialect="SQLITE")
            if layer is None:
                ds = None
                gs.fatal(_("SQL statement returned no results: {}").format(sql))
        elif vector_layer:
            layer = ds.GetLayerByName(vector_layer)
            if layer is None:
                ds = None
                gs.fatal(
                    _("Layer {} not found in {}").format(vector_layer, vector_file)
                )
        else:
            layer = ds.GetLayer(0)

        layer_defn = layer.GetLayerDefn()
        for i in range(layer_defn.GetFieldCount()):
            field_defn = layer_defn.GetFieldDefn(i)
            name = field_defn.GetName()
            type_name = field_defn.GetFieldTypeName(field_defn.GetType())
            print(f"{name} [{type_name}]")

        if sql:
            ds.ReleaseResultSet(layer)
        ds = None
        return 0

    if count_mode:
        # In counting mode, ignore attribute columns and burn 1
        column_name = None
        data_type = "Integer"
        raster_value = 1
    elif options["attribute_column"]:
        column_name = options["attribute_column"]
        data_type = get_data_type(vector_file, vector_layer, column_name, sql)
        raster_value = None
    else:
        column_name = None
        data_type = "Integer"
        raster_value = int(options["value"])

    raster = options["output"]
    memory = int(options["memory"])
    all_touched = flags["d"]

    # Compare the CRS of vector layer and region, and reproject if needed
    grass_wkt = get_grass_crs_wkt()
    vector_wkt = get_vector_crs_wkt(vector_file, vector_layer)
    match_wkt = check_wkt_match(grass_wkt, vector_wkt)
    linearize = flags["l"]

    # Reproject and/or linearize if needed (combined into a single step)
    where_consumed = False
    if not match_wkt or linearize:
        actions = []
        translate_options = {
            "format": "GPKG",
            "layers": [vector_layer] if vector_layer else None,
        }

        if where:
            translate_options["where"] = where

        if not match_wkt:
            actions.append("reprojecting")
            translate_options["dstSRS"] = grass_wkt
            translate_options["reproject"] = True

        if linearize:
            actions.append("linearizing curved geometries")
            translate_options["geometryType"] = "CONVERT_TO_LINEAR"

        # Note: -sql is not passed here,
        # sql is applied during the gdal.Rasterize step.

        gs.message(_("{} vector layer").format(" and ".join(actions).capitalize()))

        temp_vect = os.path.join(gs.tempdir(), f"{gs.tempname(4)}.gpkg")
        result = gdal.VectorTranslate(temp_vect, vector_file, **translate_options)
        if result is None:
            gs.fatal(
                _("gdal.VectorTranslate failed during: {}").format(
                    " and ".join(actions)
                )
            )
        result = None  # close dataset

        vector_file = temp_vect
        # After conversion to a single-layer GPKG, reset layer name
        # and mark where as consumed (already applied during VectorTranslate)
        vector_layer = None
        if where:
            where_consumed = True
        clean_maps.append(temp_vect)

    # Get computational region
    region_current = gs.region()

    # Get extent vector layer (if user selects option to import whole vector layer)
    if flags["v"]:
        vector = ogr.Open(vector_file)

        # Handle SQL or standard layer selection for extent
        if sql:
            vlayer = vector.ExecuteSQL(sql, dialect="SQLITE")
            if vlayer is None:
                vector = None
                gs.fatal(_("SQL statement returned no results: {}").format(sql))
        elif vector_layer:
            vlayer = vector.GetLayerByName(vector_layer)
            if vlayer is None:
                vector = None
                gs.fatal(
                    _("Layer {} not found in {}").format(vector_layer, vector_file)
                )
        else:
            vlayer = vector.GetLayer(0)

        # Apply filter so extent matches selected features
        if where:
            vlayer.SetAttributeFilter(where)

        xmin, xmax, ymin, ymax = vlayer.GetExtent()

        if sql:
            vector.ReleaseResultSet(vlayer)

        vector = None

        # Set temporary region to match the extent to that of the vector
        if not flags["r"]:
            gs.use_temp_region()
            _temp_region_used = True
        gs.run_command("g.region", flags="a", n=ymax, s=ymin, e=xmax, w=xmin)
        region_current = gs.region()

    bounds = [
        region_current["w"],
        region_current["s"],
        region_current["e"],
        region_current["n"],
    ]

    # Calculate nodata value based on data type (before setting init values)
    if data_type == "Integer":
        output_type = gdal.GDT_Int32
        nodata = 2**31 - 1
    elif data_type == "Integer64":
        gs.warning(
            "Column has Integer64 type, which is not supported by many raster formats.\n"
            "Falling back to Int32. Values > 2,147,483,647 may be truncated."
        )
        output_type = gdal.GDT_Int32
        nodata = 2**31 - 1
    elif data_type == "Real":
        output_type = gdal.GDT_Float32
        nodata = -3.40282e38
    else:
        gs.fatal(
            _(
                "The data type of the selected column is '{}'.\n"
                "To create a raster, the data type needs to be integer or float"
            ).format(data_type)
        )

    # Set the options for gdal.Rasterize()
    # Define initValues and usage of r.null based on background option and count mode

    background_opt = options.get("background")
    use_nodata_cleanup = False

    if background_opt:
        # If user provides a background value, use it and skip r.null
        init_values = [float(background_opt)]
        use_nodata_cleanup = False
    else:
        # Default behaviors if no background value provided
        if count_mode:
            # Count mode defaults to 0, no cleanup needed
            init_values = [0]
            use_nodata_cleanup = False
        else:
            # Standard mode defaults to internal nodata, require r.null cleanup
            init_values = [nodata]
            use_nodata_cleanup = True

    optim = "VECTOR" if count_mode else None

    # Fix for multi-layer datasources: explicitly select the layer when provided
    layers = [vector_layer] if vector_layer else None
    # Only pass where to Rasterize if it was not already applied during VectorTranslate
    rasterize_where = where if (where and not where_consumed) else None

    rasterize_options = gdal.RasterizeOptions(
        creationOptions=["COMPRESS=DEFLATE"],
        outputType=output_type,
        outputBounds=bounds,
        xRes=region_current["ewres"],
        yRes=region_current["nsres"],
        targetAlignedPixels=False,
        initValues=init_values,
        noData=nodata,
        allTouched=all_touched,
        attribute=column_name,
        burnValues=raster_value,
        where=rasterize_where,
        layers=layers,
        SQLStatement=sql,
        SQLDialect="SQLITE" if sql else None,
        add=count_mode,
        optim=optim,
    )

    # Define tmp raster name
    output_tif = os.path.join(gs.tempdir(), f"{gs.tempname(4)}.tif")
    clean_maps.append(output_tif)

    # Rasterize vector layer
    gs.message(_("Rasterizing, this may take a while."))
    gdal.Rasterize(output_tif, vector_file, options=rasterize_options)
    gs.message(_("Rasterization completed. Proceeding with next steps."))

    # Import in GRASS GIS
    gs.run_command(
        "r.in.gdal",
        input=output_tif,
        output=raster,
        memory=memory,
    )

    # Handling nulls
    if use_nodata_cleanup:
        gs.run_command("r.null", map=raster, setnull=nodata)

    # Create raster label
    if options["label_column"] and not count_mode:
        if data_type in ("Integer", "Integer64"):
            gs.message(_("Writing raster labels"))
            raster_labels(
                vector_file,
                vector_layer,
                raster,
                column_name,
                options["label_column"],
                where,
            )
        else:
            gs.warning(
                "The raster layer is of a float data type. No category labels can be assigned."
            )

    # Write metadata
    input_file = os.path.basename(options["input"])
    if vector_layer:
        source1 = "Based on the layer {} from the vector file {}".format(
            vector_layer, input_file
        )
    else:
        source1 = "Based on the vector file {}".format(input_file)

    if count_mode:
        source2 = "Pixel values represent the count of overlapping features"
    elif column_name:
        source2 = "Raster values are based on the values in the column {}".format(
            column_name
        )
    else:
        source2 = "User defined raster value = {}".format(raster_value)

    if where:
        source2 = "{} (filtered with where: {})".format(source2, where)
    if sql:
        source2 = "{} (filtered with SQL: {})".format(source2, sql)

    if not match_wkt:
        history = (
            "Note, the CRS of the input vector layer "
            "was reprojected to match the CRS of the mapset "
            "before converting it to a raster layer."
        )
        gs.run_command(
            "r.support",
            map=raster,
            source1=source1,
            source2=source2,
            history=history,
        )
    else:
        gs.run_command(
            "r.support",
            map=raster,
            source1=source1,
            source2=source2,
        )


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
