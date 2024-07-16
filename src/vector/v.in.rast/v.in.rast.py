#!/usr/bin/env python

############################################################################
#
# MODULE:       v.in.rast
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Convert an extrenal vector layer to a raster layer
#               using ogr2ogr, and imports the resulting raster in GRASS GIS
#
# COPYRIGHT:    (c) 2024 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Converts an external vector layer to a raster layer using ogr2ogr, and imports this raster layer.
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
# % description: OGR layer name. <br>Examples:<br>ESRI Shapefile: shapefile name<br>Geopackage: layer name
# % guisection: Input
# %end

# %option G_OPT_R_OUTPUT
# % required: yes
# %end

# %option
# % key: attribute_column
# % description: Name of attribute column that hold the values to be used as raster values (data type must be numeric)
# % guisection: Attributes
# %end

# %option
# % key: label_column
# % description: Name of attribute column that hold the values to be used as raster labels
# % guisection: Attributes
# %end

# %option
# % key: value
# % type: integer
# % description: Raster value (for use=val)
# % answer: 1
# %end

# %flag
# % key: v
# % label: Convert whole vector
# % description: Set this flag if the whole vector layer needs to be converted. By default, only the part overlapping with the computational region is converted.
# %end

# %flag
# % key: d
# % label: Create densified lines (default: thin lines)
# % description: Pixels touched by lines or polygons will be included, not just those on the line render path, or whose center point is within the polygon.
# %end

# %option G_OPT_MEMORYMB
# %end

# %rules
# % exclusive: value,attribute_column
# %end

# Import libraries
import atexit
import os
import sys
import numpy as np
from osgeo import ogr, gdal, osr
import grass.script as gs
import subprocess
from math import floor, ceil

clean_maps = []


def cleanup():
    """Remove temporary files specified in the global list"""

    for map in clean_maps:
        try:
            os.remove(map)
        except FileNotFoundError:
            print("File {} not found".format(map))
        except PermissionError:
            print("Permission denied: unable to delete {}".format(map))
        except Exception as e:
            print("An unknown error occurred: {}".format(e))


def get_grass_crs_wkt():
    """Get the CRS of the computational region"""
    # Get the projection information in WKT format
    projection_info = gs.read_command("g.proj", flags="wf")
    return projection_info.rstrip()


def get_vector_crs_wkt(vector_file):
    """Get crs of vector layer"""
    vector = ogr.Open(vector_file)
    layer = vector.GetLayer()
    spatialRef = layer.GetSpatialRef()
    if not spatialRef:
        raise ValueError("Layer does not have a spatial reference")
    vector = None
    return spatialRef.ExportToWkt()


def check_wkt_match(grass_wkt, vector_wkt):
    """
    Get the CRS of the vector layer and
    compare it with the CRS of the grass region
    """
    # Create spatial reference objects
    grass_srs = osr.SpatialReference()
    grass_srs.ImportFromWkt(grass_wkt)

    given_srs = osr.SpatialReference()
    given_srs.ImportFromWkt(vector_wkt)

    # Compare the spatial references
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
        field_name = field_definition.GetName()
        if field_name == column_name:
            field_type = field_definition.GetType()
            field_type_name = field_definition.GetFieldTypeName(field_type)
    if field_type_name is None:
        raise ValueError(
            f"Column {column_name} not found in attribute table of {vector_file}"
        )
    datasource = None
    return field_type_name


def raster_labels(vector_file, layer_name, raster, column_name, column_rat):
    """Add labels to raster layer"""

    # Read the attribute data from the vector layer
    datasource = ogr.Open(vector_file)
    if layer_name:
        layer = datasource.GetLayerByName(layer_name)
        if layer is None:
            datasource = None
            raise ValueError(f"Layer {layer_name} not found in {vector_file}")
    else:
        layer = datasource.GetLayer(0)

    ids = []
    labels = []

    for feature in layer:
        feature_id = feature.GetFID()
        if (
            feature.GetField(column_name) is not None
            and feature.GetField(column_rat) is not None
        ):
            ids.append(feature.GetField(column_name))
            labels.append(feature.GetField(column_rat))
    datasource = None  # Close the vector dataset

    # Print warning if number of unique ids do not match number of unique labels
    if len(np.unique(ids)) < len(np.unique(labels)):
        gs.warning(
            _(
                "The number of unique raster values (based on column '{0}') is smaller "
                "than the number of unique labels in the column '{1}'. This means "
                "that there are raster value with more than one matching label."
                "For those raster values, the first label in column '{1}' is used.".format(
                    column_name, column_rat
                )
            )
        )

    # Create category rules
    unique_ids = {}
    for i in range(len(ids)):
        if ids[i] not in unique_ids:
            unique_ids[ids[i]] = labels[i]

    cat_rules = "\n".join(
        ["{0}|{1}".format(key, value) for key, value in unique_ids.items()]
    )

    gs.write_command(
        "r.category", map=raster, rules="-", stdin=cat_rules, separator="pipe"
    )


def main(options, flags):

    ogr.UseExceptions()

    # Get variables
    vector_file = options["input"]
    vector_layer = options["layer"]
    if options["attribute_column"]:
        column_name = options["attribute_column"]
        data_type = get_data_type(vector_file, vector_layer, column_name)
        raster_value = None
    else:
        column_name = None
        data_type = "Integer"
        raster_value = int(options["value"])
    raster = options["output"]
    output_tif = os.path.join(gs.tempdir(), f"{gs.tempname(4)}.tif")
    clean_maps.append(output_tif)
    memory = int(options["memory"])
    all_touched = flags["d"]

    # Compare the CRS of vector layer and region, and reproject if needed
    grass_wkt = get_grass_crs_wkt()
    vector_wkt = get_vector_crs_wkt(vector_file)
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
        reproj = subprocess.run(ogr2ogr_command, text=True)
        if reproj.returncode != 0:
            raise RuntimeError("ogr2ogr command failed")
        vector_file = temp_vect
        clean_maps.append(temp_vect)

    # Get computational region
    region = gs.region()

    # Get extent vector layer (if user selects option to import whole vector layer)
    if flags["v"]:
        vector = ogr.Open(vector_file)
        vlayer = vector.GetLayer()
        xmin, xmax, ymin, ymax = vlayer.GetExtent()

        if region["s"] != ymin:
            south_limit = (
                region["s"]
                + floor((ymin - region["s"]) / region["nsres"]) * region["nsres"]
            )
        else:
            south_limit = ymin

        if region["n"] != ymax:
            north_limit = (
                region["n"]
                + ceil((ymax - region["n"]) / region["nsres"]) * region["nsres"]
            )
        else:
            north_limit = ymax

        if region["w"] != xmin:
            west_limit = (
                region["w"]
                + floor((xmin - region["w"]) / region["ewres"]) * region["ewres"]
            )
        else:
            west_limit = xmin

        if region["e"] != xmax:
            east_limit = (
                region["e"]
                + ceil((xmax - region["e"]) / region["ewres"]) * region["ewres"]
            )
        else:
            east_limit = xmax
        bounds = [west_limit, south_limit, east_limit, north_limit]
    else:
        bounds = [region["w"], region["s"], region["e"], region["n"]]

    # Set the options for gdal.Rasterize() with gdal.RasterizeOptions()
    if data_type == "Integer":
        output_type = gdal.GDT_Int32
        nodata = 2**31 - 1
    elif data_type == "Real":
        output_type = gdal.GDT_Float32
        nodata = -3.40282e38
    else:
        gs.fatal(
            _(
                "The data type of the selected column is '{}'.\n"
                "To create a raster, the data type needs to be integer or float".format(
                    data_type
                )
            )
        )

    rasterize_options = gdal.RasterizeOptions(
        creationOptions=["COMPRESS=DEFLATE"],
        outputType=output_type,
        outputBounds=bounds,
        xRes=region["ewres"],
        yRes=region["nsres"],
        targetAlignedPixels=False,
        initValues=[nodata],
        noData=nodata,
        allTouched=all_touched,
        attribute=column_name,
        burnValues=raster_value,
    )

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
        if data_type == "Integer":
            gs.message(_("Writing raster labels"))
            raster_labels(
                vector_file, vector_layer, raster, column_name, options["label_column"]
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
