#!/usr/bin/env python


############################################################################
#
# MODULE:       r.mblend
#
# AUTHOR(S):    Luís Moreira de Sousa
#
# PURPOSE:      Blends two rasters of different spatial resolution.
#
# COPYRIGHT:    (c) 2017 Luís Moreira de Sousa
#
#               This programme is released under the European Union Public
#               Licence v 1.1. Please consult the LICENCE file for details.
#
#############################################################################

# %module
# % description: Blends two rasters of different spatial resolution.
# % keyword: raster
# % keyword: resolution
# %end
# %option HIGH
# % key: high
# % description: High resolution input raster.
# %end
# %option LOW
# % key: low
# % label: Low resolution input raster.
# %end
# %option OUTPUT
# % key: output
# % label: Name of output raster.
# %end
# %option FAR_EDGE
# % key: far_edge
# % key_desc: value
# % type: double
# % label: Percentage of distance to high resolution raster used to determine far edge. Number between 0 and 100.
# % description: When the blending occurs along a single edge a number closer to 100 tends to produce more even results. With more blending edges (e.g. high resolution DEM sits on the middle of the low resolution DEM) a lower number may produce a more regular blend.
# % answer: 95
# % multiple: no
# % required: no
# %end
# %option INTER_POINTS
# % key: inter_points
# % key_desc: value
# % type: integer
# % label: Number of points to use in interpolation.
# % description: A higher number produces a smoother result but requires a lengthier computation.
# % answer: 50
# % multiple: no
# % required: no
# %end
# %flag
# % key: a
# % label: Assign the average difference between the two rasters to the far edge (instead of zero).
# %end

import os
import atexit
import math
from time import gmtime, strftime
import grass.script as gscript

index = 0
far_edge_value = "0"
d_max = None
TMP_MAPS = []
WEIGHT_MAX = 10000
COL_VALUE = "value"
COL_FLAG = "flag"


def getTemporaryIdentifier():
    global index
    global TMP_MAPS
    id = "tmp_" + str(os.getpid()) + str(index)
    index = index + 1
    TMP_MAPS.append(id)
    return id


def cleanup():
    while len(TMP_MAPS) > 0:
        gscript.run_command(
            "g.remove", type="all", name=TMP_MAPS.pop(), flags="f", quiet=True
        )


def compute_d_max(region):
    global d_max
    print("Region:\n" + str(region))
    d_max = (
        math.sqrt(
            math.pow(region["w"] - region["e"], 2)
            + math.pow(region["n"] - region["s"], 2)
        )
        / 100
    )


def main():
    global far_edge_value
    global d_max

    options, flags = gscript.parser()
    high = options["high"]
    low = options["low"]
    output = options["output"]
    far_edge = float(options["far_edge"])
    inter_points = int(options["inter_points"])
    use_average_differences = flags["a"]

    if high is None or high == "":
        gscript.error(_("[r.mblend] ERROR: high is a mandatory parameter."))
        exit()

    if low is None or low == "":
        gscript.error(_("[r.mblend] ERROR: low is a mandatory parameter."))
        exit()

    if output is None or output == "":
        gscript.error(_("[r.mblend] ERROR: output is a mandatory parameter."))
        exit()

    if far_edge < 0 or far_edge > 100:
        gscript.error(
            _("[r.mblend] ERROR: far_edge must be a percentage", " between 0 and 100.")
        )
        exit()

    if inter_points < 0:
        gscript.error(
            _("[r.mblend] ERROR: inter_points must be a positive", " integer.")
        )
        exit()

    # Set the region to the two input rasters
    gscript.run_command("g.region", raster=high + "," + low)
    # Determine cell side
    region = gscript.region()
    if region["nsres"] > region["ewres"]:
        cell_side = region["nsres"]
    else:
        cell_side = region["ewres"]

    compute_d_max(region)

    # Make cell size compatible
    low_res_inter = getTemporaryIdentifier()
    gscript.message(
        _("[r.mblend] Resampling low resolution raster to higher" + " resolution")
    )
    gscript.run_command(
        "r.resamp.interp", input=low, output=low_res_inter, method="nearest"
    )

    # Obtain extent to interpolate
    low_extent_rast = getTemporaryIdentifier()
    high_extent_rast = getTemporaryIdentifier()
    low_extent = getTemporaryIdentifier()
    high_extent = getTemporaryIdentifier()
    interpol_area = getTemporaryIdentifier()
    gscript.message(_("[r.mblend] Multiplying low resolution by zero"))
    gscript.mapcalc(low_extent_rast + " = " + low + " * 0")
    gscript.message(_("[r.mblend] Multiplying high resolution by zero"))
    gscript.mapcalc(high_extent_rast + " = " + high + " * 0")
    gscript.message(_("[r.mblend] Computing extent of low resolution"))
    gscript.run_command(
        "r.to.vect", input=low_extent_rast, output=low_extent, type="area"
    )
    gscript.message(_("[r.mblend] Computing extent of high resolution"))
    gscript.run_command(
        "r.to.vect", input=high_extent_rast, output=high_extent, type="area"
    )
    gscript.message(_("[r.mblend] Computing area to interpolate"))
    gscript.run_command(
        "v.overlay",
        ainput=low_extent,
        binput=high_extent,
        output=interpol_area,
        operator="not",
    )

    # Compute difference between the two rasters and vectorise to points
    interpol_area_buff = getTemporaryIdentifier()
    diff = getTemporaryIdentifier()
    diff_points_edge = getTemporaryIdentifier()
    gscript.mapcalc(diff + " = " + high + " - " + low_res_inter)
    gscript.message(_("[r.mblend] Computing buffer around interpolation area"))
    gscript.run_command(
        "v.buffer",
        input=interpol_area,
        output=interpol_area_buff,
        type="area",
        distance=cell_side,
    )
    gscript.message(_("[r.mblend] Vectorising differences between input" + " rasters"))
    gscript.run_command("r.mask", vector=interpol_area_buff)
    gscript.run_command("r.to.vect", input=diff, output=diff_points_edge, type="point")
    gscript.run_command("r.mask", flags="r")

    # Compute average of the differences if flag -a was passed
    if use_average_differences:
        p = gscript.pipe_command("r.univar", map=diff)
        result = {}
        for line in p.stdout:
            vector = line.split(": ")
            if vector[0] == "mean":
                print("Found it: " + vector[1])
                far_edge_value = vector[1]
        p.wait()

    # Get points in low resolution farther away from high resolution raster
    dist_high = getTemporaryIdentifier()
    weights = getTemporaryIdentifier()
    interpol_area_inner_buff = getTemporaryIdentifier()
    interpol_area_points = getTemporaryIdentifier()
    pre_interpol_area_points = getTemporaryIdentifier()
    weight_points = getTemporaryIdentifier()
    interpol_area_in_buff = getTemporaryIdentifier()
    weight_points_all_edges = getTemporaryIdentifier()
    weight_points_edge = getTemporaryIdentifier()
    # 1. Distance to High resolution raster
    gscript.message(_("[r.mblend] Computing distance to high resolution" + " raster"))
    gscript.run_command("r.grow.distance", input=high, distance=dist_high)
    # 2. Rescale to the interval [0,10000]: these are the weights
    gscript.message(_("[r.mblend] Rescaling distance to [0,10000] interval"))
    gscript.run_command(
        "r.rescale", input=dist_high, output=weights, to="0," + str(WEIGHT_MAX)
    )
    # 3. Extract points from interpolation area border
    gscript.message(
        _("[r.mblend] Extract points from interpolation area " + "boundary")
    )
    inner_buff = -cell_side / 2
    gscript.run_command(
        "v.buffer",
        input=interpol_area,
        output=interpol_area_inner_buff,
        type="area",
        distance=inner_buff,
    )
    gscript.run_command(
        "v.to.points",
        input=interpol_area_inner_buff,
        output=pre_interpol_area_points,
        type="boundary",
        dmax=d_max,
        layer="-1",
    )
    gscript.message(_("[r.mblend] Copying features to layer 1"))
    gscript.run_command(
        "v.category",
        input=pre_interpol_area_points,
        output=interpol_area_points,
        option="chlayer",
        layer="2,1",
    )
    gscript.message(_("[r.mblend] Linking attribute table to layer 1"))
    gscript.run_command(
        "v.db.connect",
        map=interpol_area_points,
        table=interpol_area_points,
        layer="1",
        overwrite=True,
    )
    # 4. Query distances to interpolation area points
    gscript.message(_("[r.mblend] Querying distances raster"))
    gscript.run_command(
        "v.what.rast", map=interpol_area_points, raster=weights, column=COL_VALUE
    )
    # 5. Select those with higher weights
    cut_off = str(far_edge / 100 * WEIGHT_MAX)
    gscript.message(
        _("[r.mblend] Selecting far edge points (using cut-off" + " percentage)")
    )
    gscript.run_command(
        "v.extract",
        input=interpol_area_points,
        output=weight_points_edge,
        where=COL_VALUE + ">" + cut_off,
    )

    # Merge the two point edges and set low res edge to zero
    points_edges = getTemporaryIdentifier()
    gscript.message(_("[r.mblend] Dropping extra column from far edge"))
    gscript.run_command(
        "v.db.dropcolumn", map=weight_points_edge, layer="1", columns="along"
    )
    gscript.message(_("[r.mblend] Setting far edge weights to zero"))
    gscript.run_command(
        "v.db.update", map=weight_points_edge, column=COL_VALUE, value=far_edge_value
    )
    gscript.message(_("[r.mblend] Patching the two edges"))
    gscript.run_command(
        "v.patch",
        input=diff_points_edge + "," + weight_points_edge,
        output=points_edges,
        flags="e",
    )

    # Interpolate smoothing raster
    smoothing = getTemporaryIdentifier()
    interpol_area_rst = getTemporaryIdentifier()
    # Consign region to interpolation area
    gscript.run_command("g.region", vector=interpol_area_buff)
    gscript.message(
        _("[r.mblend] Interpolating smoothing surface. This" + " might take a while...")
    )
    gscript.run_command(
        "v.surf.idw",
        input=points_edges,
        column=COL_VALUE,
        output=smoothing,
        power=2,
        npoints=inter_points,
    )
    # Reset region to full extent
    gscript.run_command("g.region", raster=high + "," + low)

    # Apply stitching
    smooth_low_res = getTemporaryIdentifier()
    # Sum to low res
    gscript.message(_("[r.mblend] Applying smoothing surface"))
    gscript.mapcalc(smooth_low_res + " = " + low_res_inter + " + " + smoothing)
    # Add both rasters
    try:
        gscript.message(_("[r.mblend] Joining result into a single raster"))
        gscript.run_command("r.patch", input=high + "," + smooth_low_res, output=output)
    except Exception as ex:
        gscript.error(_("[r.mblend] ERROR: Failed to create smoothed raster."))
        exit()

    gscript.message(_("[r.mblend] SUCCESS: smoothed raster created."))


if __name__ == "__main__":
    atexit.register(cleanup)
    gscript.use_temp_region()
    main()
