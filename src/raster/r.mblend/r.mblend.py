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
import grass.script as gs

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
        gs.run_command(
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

    options, flags = gs.parser()
    high = options["high"]
    low = options["low"]
    output = options["output"]
    far_edge = float(options["far_edge"])
    inter_points = int(options["inter_points"])
    use_average_differences = flags["a"]

    if high is None or high == "":
        gs.error(_("[r.mblend] ERROR: high is a mandatory parameter."))
        exit()

    if low is None or low == "":
        gs.error(_("[r.mblend] ERROR: low is a mandatory parameter."))
        exit()

    if output is None or output == "":
        gs.error(_("[r.mblend] ERROR: output is a mandatory parameter."))
        exit()

    if far_edge < 0 or far_edge > 100:
        gs.error(
            _("[r.mblend] ERROR: far_edge must be a percentage", " between 0 and 100.")
        )
        exit()

    if inter_points < 0:
        gs.error(_("[r.mblend] ERROR: inter_points must be a positive", " integer."))
        exit()

    # Set the region to the two input rasters
    gs.run_command("g.region", raster=high + "," + low)
    # Determine cell side
    region = gs.region()
    if region["nsres"] > region["ewres"]:
        cell_side = region["nsres"]
    else:
        cell_side = region["ewres"]

    compute_d_max(region)

    # Make cell size compatible
    low_res_inter = getTemporaryIdentifier()
    gs.message(
        _("[r.mblend] Resampling low resolution raster to higher" + " resolution")
    )
    gs.run_command("r.resamp.interp", input=low, output=low_res_inter, method="nearest")

    # Obtain extent to interpolate
    low_extent_rast = getTemporaryIdentifier()
    high_extent_rast = getTemporaryIdentifier()
    low_extent = getTemporaryIdentifier()
    high_extent = getTemporaryIdentifier()
    interpol_area = getTemporaryIdentifier()
    gs.message(_("[r.mblend] Multiplying low resolution by zero"))
    gs.mapcalc(low_extent_rast + " = " + low + " * 0")
    gs.message(_("[r.mblend] Multiplying high resolution by zero"))
    gs.mapcalc(high_extent_rast + " = " + high + " * 0")
    gs.message(_("[r.mblend] Computing extent of low resolution"))
    gs.run_command("r.to.vect", input=low_extent_rast, output=low_extent, type="area")
    gs.message(_("[r.mblend] Computing extent of high resolution"))
    gs.run_command("r.to.vect", input=high_extent_rast, output=high_extent, type="area")
    gs.message(_("[r.mblend] Computing area to interpolate"))
    gs.run_command(
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
    gs.mapcalc(diff + " = " + high + " - " + low_res_inter)
    gs.message(_("[r.mblend] Computing buffer around interpolation area"))
    gs.run_command(
        "v.buffer",
        input=interpol_area,
        output=interpol_area_buff,
        type="area",
        distance=cell_side,
    )
    gs.message(_("[r.mblend] Vectorising differences between input" + " rasters"))
    gs.run_command("r.mask", vector=interpol_area_buff)
    gs.run_command("r.to.vect", input=diff, output=diff_points_edge, type="point")
    gs.run_command("r.mask", flags="r")

    # Compute average of the differences if flag -a was passed
    if use_average_differences:
        p = gs.pipe_command("r.univar", map=diff)
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
    gs.message(_("[r.mblend] Computing distance to high resolution" + " raster"))
    gs.run_command("r.grow.distance", input=high, distance=dist_high)
    # 2. Rescale to the interval [0,10000]: these are the weights
    gs.message(_("[r.mblend] Rescaling distance to [0,10000] interval"))
    gs.run_command(
        "r.rescale", input=dist_high, output=weights, to="0," + str(WEIGHT_MAX)
    )
    # 3. Extract points from interpolation area border
    gs.message(_("[r.mblend] Extract points from interpolation area " + "boundary"))
    inner_buff = -cell_side / 2
    gs.run_command(
        "v.buffer",
        input=interpol_area,
        output=interpol_area_inner_buff,
        type="area",
        distance=inner_buff,
    )
    gs.run_command(
        "v.to.points",
        input=interpol_area_inner_buff,
        output=pre_interpol_area_points,
        type="boundary",
        dmax=d_max,
        layer="-1",
    )
    gs.message(_("[r.mblend] Copying features to layer 1"))
    gs.run_command(
        "v.category",
        input=pre_interpol_area_points,
        output=interpol_area_points,
        option="chlayer",
        layer="2,1",
    )
    gs.message(_("[r.mblend] Linking attribute table to layer 1"))
    gs.run_command(
        "v.db.connect",
        map=interpol_area_points,
        table=interpol_area_points,
        layer="1",
        flags="o",
    )
    # 4. Query distances to interpolation area points
    gs.message(_("[r.mblend] Querying distances raster"))
    gs.run_command(
        "v.what.rast", map=interpol_area_points, raster=weights, column=COL_VALUE
    )
    # 5. Select those with higher weights
    cut_off = str(far_edge / 100 * WEIGHT_MAX)
    gs.message(
        _("[r.mblend] Selecting far edge points (using cut-off" + " percentage)")
    )
    gs.run_command(
        "v.extract",
        input=interpol_area_points,
        output=weight_points_edge,
        where=COL_VALUE + ">" + cut_off,
    )

    # Merge the two point edges and set low res edge to zero
    points_edges = getTemporaryIdentifier()
    gs.message(_("[r.mblend] Dropping extra column from far edge"))
    gs.run_command(
        "v.db.dropcolumn", map=weight_points_edge, layer="1", columns="along"
    )
    gs.message(_("[r.mblend] Setting far edge weights to zero"))
    gs.run_command(
        "v.db.update", map=weight_points_edge, column=COL_VALUE, value=far_edge_value
    )
    gs.message(_("[r.mblend] Patching the two edges"))
    gs.run_command(
        "v.patch",
        input=diff_points_edge + "," + weight_points_edge,
        output=points_edges,
        flags="e",
    )

    # Interpolate smoothing raster
    smoothing = getTemporaryIdentifier()
    interpol_area_rst = getTemporaryIdentifier()
    # Consign region to interpolation area
    gs.run_command("g.region", vector=interpol_area_buff)
    gs.message(
        _("[r.mblend] Interpolating smoothing surface. This" + " might take a while...")
    )
    gs.run_command(
        "v.surf.idw",
        input=points_edges,
        column=COL_VALUE,
        output=smoothing,
        power=2,
        npoints=inter_points,
    )
    # Reset region to full extent
    gs.run_command("g.region", raster=high + "," + low)

    # Apply stitching
    smooth_low_res = getTemporaryIdentifier()
    # Sum to low res
    gs.message(_("[r.mblend] Applying smoothing surface"))
    gs.mapcalc(smooth_low_res + " = " + low_res_inter + " + " + smoothing)
    # Add both rasters
    try:
        gs.message(_("[r.mblend] Joining result into a single raster"))
        gs.run_command("r.patch", input=high + "," + smooth_low_res, output=output)
    except Exception as ex:
        gs.error(_("[r.mblend] ERROR: Failed to create smoothed raster."))
        exit()

    gs.message(_("[r.mblend] SUCCESS: smoothed raster created."))


if __name__ == "__main__":
    atexit.register(cleanup)
    gs.use_temp_region()
    main()
