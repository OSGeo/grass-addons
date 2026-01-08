#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.in.vect
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Convert an external vector layer to a raster layer
#               using gdal.Rasterize, and imports the resulting raster in GRASS GIS
#
# COPYRIGHT:    (c) 2024 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Converts an external vector layer to a raster layer using gdal.Rasterize (the vector layer will be reprojected first if its CRS is different from the current mapset), and imports this raster layer.
# % keyword: vector
# % keyword: raster
# % keyword: import
# % keyword: convert
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
# % guisection: Attributes
# %end

# %option G_OPT_DB_COLUMN
# % key: label_column
# % label: Column with raster labels
# % description: Name of attribute column that hold the values to be used as raster labels
# % guisection: Attributes
# %end

# %option G_OPT_DB_WHERE
# % description: Attribute query for selecting features (without the WHERE keyword), e.g. "type = 'road' AND status = 1"
# % guisection: Selection
# % required: no
# %end

# %option
# % key: value
# % type: integer
# % label: Raster value
# % description: Raster value (if attribute_column is left empty)
# %end

# %flag
# % key: v
# % label: Convert whole vector
# % description: Set this flag if the whole vector layer needs to be converted. By default, only the part overlapping with the computational region is converted.
# %end

# %flag
# % key: a
# % label: Match region to vector bounding box
# % description: Set region extent to match that of the bounding box of the vector layer.
# %end

# %flag
# % key: d
# % label: Create densified lines
# % description: Pixels touched by lines or polygons will be included, not just those on the line render path, or whose center point is within the polygon  (default: thin lines).
# %end

# %option G_OPT_MEMORYMB
# %end

# %rules
# % requires_all: -a,-v
# %end

# %rules
# % required: value,attribute_column
# %end

# %rules
# % exclusive: value,attribute_column
# %end

# Libraries
import atexit
import os
import sys
import numpy as np
from osgeo import ogr, gdal, osr
import grass.script as gs
import subprocess

clean_maps = []
_temp_region_used = False


def cleanup():
    """Remove temporary files specified in the global list (and delete temp region if used)."""
    global _temp_region_used

    for path in clean_maps:
        try:
            os.remove(path)
        except FileNotFoundError:
            gs.warning(_("Temporary file not found: {}").format(path))
        except PermissionError:
            gs.warning(_("Permission denied: unable to delete {}").format(path))
        except Exception as e:
            gs.warning(_("Unable to delete temporary file {}: {}").format(path, e))

    # ensure temp region is deleted if we created one
    if _temp_region_used:
        try:
            gs.del_temp_region()
        except Exception as e:
            gs.warning(_("Unable to delete temporary region: {}").format(e))


def get_grass_crs_wkt():
    """Get the CRS of the computational region"""

    # Get the projection information in WKT format
    projection_info = gs.read_command("g.proj", flags="wf")
    return projection_info.rstrip()


def get_vector_crs_wkt(vector_file, layer_name=None):
    """Get CRS (WKT) of selected vector layer)"""
    vector = ogr.Open(vector_file)
    if vector is None:
        raise FileNotFoundError(f"Could not open {vector_file}")

    if layer_name:
        layer = vector.GetLayerByName(layer_name)
        if layer is None:
            vector = None
            raise ValueError(f"Layer {layer_name} not found in {vector_file}")
    else:
        layer = vector.GetLayer(0)

    spatialRef = layer.GetSpatialRef()
    if not spatialRef:
        vector = None
        raise ValueError("Layer does not have a spatial reference")

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


def get_data_type(vector_file, layer_name, column_name):
    """Get the data type of the selected column"""
    # Open the vector file
    datasource = ogr.Open(vector_file, 0)
    if datasource is None:
        raise FileNotFoundError(f"Could not open {vector_file}")

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

    # Iterate through fields to find the specified column
    field_type_name = None
    for i in range(field_count):
        field_definition = layer_definition.GetFieldDefn(i)
        if field_definition.GetName() == column_name:
            field_type = field_definition.GetType()
            field_type_name = field_definition.GetFieldTypeName(field_type)

    datasource = None

    if field_type_name is None:
        raise ValueError(
            f"Column {column_name} not found in attribute table of {vector_file}"
        )

    return field_type_name


def raster_labels(vector_file, layer_name, raster, column_name, column_rat, where=None):
    """Add labels to raster layer"""
    datasource = ogr.Open(vector_file)
    if layer_name:
        layer = datasource.GetLayerByName(layer_name)
        if layer is None:
            datasource = None
            raise ValueError(f"Layer {layer_name} not found in {vector_file}")
    else:
        layer = datasource.GetLayer(0)

    # Apply optional attribute filter so labels match the selected subset
    if where:
        layer.SetAttributeFilter(where)

    ids = []
    labels = []

    for feature in layer:
        if (
            feature.GetField(column_name) is not None
            and feature.GetField(column_rat) is not None
        ):
            ids.append(feature.GetField(column_name))
            labels.append(feature.GetField(column_rat))

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

    ogr.UseExceptions()

    # Get variables
    vector_file = options["input"]
    vector_layer = options["layer"] or None
    where = options.get("where") or None

    if options["attribute_column"]:
        column_name = options["attribute_column"]
        data_type = get_data_type(vector_file, vector_layer, column_name)
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

    if not match_wkt:
        gs.message(
            _("reprojecting vector layer to match the CRS of the current mapset")
        )
        temp_vect = os.path.join(gs.tempdir(), f"{gs.tempname(4)}.gpkg")

        ogr2ogr_command = [
            "ogr2ogr",
            "-f",
            "GPKG",
            "-t_srs",
            grass_wkt,
            temp_vect,
            vector_file,
        ]
        if vector_layer:
            ogr2ogr_command.append(vector_layer)

        if where:
            ogr2ogr_command.extend(["-where", where])

        # Safety: raise immediately on failure
        subprocess.run(ogr2ogr_command, text=True, check=True)

        vector_file = temp_vect
        clean_maps.append(temp_vect)

    # Get computational region
    region_current = gs.region()

    # Get extent vector layer (if user selects option to import whole vector layer)
    if flags["v"]:
        vector = ogr.Open(vector_file)

        if vector_layer:
            vlayer = vector.GetLayerByName(vector_layer)
            if vlayer is None:
                vector = None
                raise ValueError(f"Layer {vector_layer} not found in {vector_file}")
        else:
            vlayer = vector.GetLayer(0)

        # Apply filter so extent matches selected features
        if where:
            vlayer.SetAttributeFilter(where)

        xmin, xmax, ymin, ymax = vlayer.GetExtent()
        vector = None

        # Set temporary region to match the extent to that of the vector
        if not flags["a"]:
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

    # Set the options for gdal.Rasterize()
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

    # Fix for multi-layer datasources: explicitly select the layer when provided
    layers = [vector_layer] if vector_layer else None

    rasterize_options = gdal.RasterizeOptions(
        creationOptions=["COMPRESS=DEFLATE"],
        outputType=output_type,
        outputBounds=bounds,
        xRes=region_current["ewres"],
        yRes=region_current["nsres"],
        targetAlignedPixels=False,
        initValues=[nodata],
        noData=nodata,
        allTouched=all_touched,
        attribute=column_name,
        burnValues=raster_value,
        where=where,
        layers=layers,
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
    gs.run_command("r.null", map=raster, setnull=nodata)

    # Create raster label
    if options["label_column"]:
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

    if column_name:
        source2 = "Raster values are based on the values in the column {}".format(
            column_name
        )
    else:
        source2 = "User defined raster value = {}".format(raster_value)

    if where:
        source2 = "{} (filtered with where: {})".format(source2, where)

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
