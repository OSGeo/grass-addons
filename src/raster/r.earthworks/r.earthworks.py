#!/usr/bin/env python

##############################################################################
# MODULE:    r.earthworks
#
# AUTHOR(S): Brendan Harmon <brendan.harmon@gmail.com>
#
# PURPOSE:   Terrain modeling with cut and fill operations
#
# COPYRIGHT: (C) 2024 by Brendan Harmon and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""Earthworks"""

# %module
# % description: Terrain modeling with cut and fill operations
# % keyword: raster
# % keyword: terrain
# % keyword: earthwork
# %end

# %option G_OPT_R_INPUT
# % key: elevation
# % description: Input elevation raster
# % label: Input elevation raster
# %end

# %option G_OPT_R_OUTPUT
# % key: earthworks
# % answer: earthworks
# % description: Output elevation raster
# % label: Output earthworks
# % answer: earthworks
# %end

# %option
# % key: mode
# % type: string
# % answer: absolute
# % options: relative,absolute
# % description: Earthworking mode
# % descriptions: relative;Relative to existing topography;absolute;At given elevation
# % required: yes
# %end

# %option
# % key: operation
# % type: string
# % answer: cutfill
# % options: cut,fill,cutfill
# % description: Earthworking operation
# % descriptions: cut;Cut into topography;fill;Fill over topography;cutfill;Cut and fill
# % required: yes
# %end

# %option
# % key: function
# % type: string
# % answer: linear
# % options: linear,exponential,logistic,gaussian,lorentz,quadratic,cubic
# % description: Slope function
# % descriptions: linear;linear decay function;exponential;Exponential decay function;logistic;Logistic function;gaussian;Gaussian function;lorentz;Cauchy-Lorentz distribution;quadratic;Quadratic function;cubic;Cubic function
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % key: raster
# % description: Input raster spot elevations
# % label: Input raster spot elevations
# % required: no
# % guisection: Input
# %end

# %option G_OPT_M_COORDS
# % key: coordinates
# % description: Seed point coordinates
# % label: Seed point coordinates
# % required: no
# % guisection: Input
# %end

# %option G_OPT_V_INPUT
# % key: points
# % label: Input points
# % description: Input points
# % required: no
# % guisection: Input
# %end

# %option G_OPT_V_INPUT
# % key: lines
# % label: Input lines
# % description: Input lines
# % required: no
# % guisection: Input
# %end

# %option
# % key: z
# % type: double
# % description: Elevation value
# % label: Elevation value
# % answer: 0.0
# % multiple: yes
# % guisection: Input
# %end

# %option
# % key: flat
# % type: double
# % description: Radius of flats
# % label: Radius of flats
# % answer: 0.0
# % multiple: no
# % guisection: Input
# %end

# %option G_OPT_R_OUTPUT
# % key: volume
# % description: Output volumetric change raster
# % label: Output volume
# % required: no
# % guisection: Output
# %end

# %option
# % key: linear
# % type: double
# % description: Linear slope
# % label: Linear slope
# % answer: 0.1
# % multiple: no
# % guisection: Slope
# %end

# %option
# % key: exponential
# % type: double
# % description: Exponential decay factor
# % label: Exponential decay factor
# % answer: 0.04
# % multiple: no
# % guisection: Slope
# %end

# %option
# % key: logistic
# % type: double
# % description: Logistic shape parameter
# % label: Logistic shape parameter
# % answer: 0.025
# % multiple: no
# % guisection: Slope
# %end

# %option
# % key: gaussian
# % type: double
# % description: Gaussian standard deviation
# % label: Gaussian standard deviation
# % answer: 25
# % multiple: no
# % guisection: Slope
# %end

# %option
# % key: lorentz
# % type: double
# % description: Cauchy-Lorentz scale parameter
# % label: Cauchy-Lorentz scale parameter
# % answer: 25
# % multiple: no
# % guisection: Slope
# %end

# %option
# % key: quadratic
# % type: double
# % description: Quadratic coefficient
# % label: Quadratic coefficient
# % answer: 0.001
# % multiple: no
# % guisection: Slope
# %end

# %option
# % key: cubic
# % type: double
# % description: Cubic coefficient
# % label: Cubic coefficient
# % answer: 0.00001
# % multiple: no
# % guisection: Slope
# %end

# %option
# % key: threshold
# % type: double
# % description: Threshold per quadrant
# % label: Threshold per quadrant
# % answer: 500
# % multiple: no
# % guisection: Quadtree
# %end

# %option
# % key: border
# % type: double
# % description: Border around quadrants
# % label: Border around quadrants
# % answer: 250
# % multiple: no
# % guisection: Quadtree
# %end

# %flag
# % key: p
# % description: Print volume
# %end

# %flag
# % key: d
# % description: Disable quadtree segmentation
# %end

# %rules
# % required: raster,coordinates,points,lines
# % exclusive: raster,coordinates,points,lines
# %end

# Import libraries
import grass.script as gs
import numpy as np
import sys
import atexit
import math

# Set global variables
temporary = []
id = gs.append_uuid("source")
source = id


def quadtree(coordinates, threshold, regions, cloud):
    """Quadtree segmentation"""

    # Construct quadtree
    subdivision(coordinates, threshold, regions, cloud)

    # Prune quadtree
    regions, cloud = prune(threshold, regions, cloud)

    return regions, cloud


def subdivision(coordinates, threshold, regions, cloud):
    """Recursively subdivide region into quadrants"""

    # Find bounds of current region
    gregion = gs.region()
    n = gregion["n"]
    s = gregion["s"]
    e = gregion["e"]
    w = gregion["w"]

    # Find current extent
    x = e - w
    y = n - s

    # Set parameters
    counter = len(regions) + 1
    region = f"temporary_region_{counter}"

    # Find points in quadrant
    coordinates, count = points_in_region(coordinates, region, n, s, e, w)

    # Check quadrant for points
    if count is not None and count > 0:
        # Append lists
        regions.append(region)
        cloud.append(coordinates)

    # Discard empty quadrant
    else:
        gs.run_command(
            "g.remove", type="region", name=region, flags="f", superquiet=True
        )

    # Check point count against threshold
    if count > threshold:
        # Subdivide quadrants
        quadrants = ["nw", "ne", "sw", "se"]
        for quad in quadrants:
            # Subdivide quadrant
            quadrant(quad, regions, cloud, n, s, e, w, x, y, coordinates, threshold)


def quadrant_nw(region, n, s, e, w, x, y):
    """Set north west quadrant"""

    # Set region to north west quadrant
    gs.run_command("g.region", n=n, s=n - y / 2, e=w + x / 2, w=w, save=region)


def quadrant_ne(region, n, s, e, w, x, y):
    """Set north east quadrant"""

    # Set region to north east quadrant
    gs.run_command("g.region", n=n, s=n - y / 2, e=e, w=e - x / 2, save=region)


def quadrant_sw(region, n, s, e, w, x, y):
    """Set south west quadrant"""

    # Set region to south west quadrant
    gs.run_command("g.region", n=s + y / 2, s=s, e=w + x / 2, w=w, save=region)


def quadrant_se(region, n, s, e, w, x, y):
    """Set south east quadrant"""

    # Set region to south east quadrant
    gs.run_command("g.region", n=s + y / 2, s=s, e=e, w=e - x / 2, save=region)


def quadrant(quad, regions, cloud, n, s, e, w, x, y, coordinates, threshold):
    """Recursively subdivide quadrant"""

    # Set parameters
    counter = len(regions) + 1
    region = f"temporary_region_{counter}"

    # Set quadrant
    if quad == "nw":
        quadrant_nw(region, n, s, e, w, x, y)
    if quad == "ne":
        quadrant_ne(region, n, s, e, w, x, y)
    if quad == "sw":
        quadrant_sw(region, n, s, e, w, x, y)
    if quad == "se":
        quadrant_se(region, n, s, e, w, x, y)
    gs.run_command("g.region", region=region)

    # Subdivide quadrant
    subdivision(coordinates, threshold, regions, cloud)


def points_in_region(coordinates, region, north, south, east, west):
    """Find points in region"""

    # Create empty lists of coordinates
    u = []
    v = []
    w = []

    # Find coordinates in current region
    for x, y, z in coordinates:
        if x <= east and x >= west and y <= north and y >= south:
            u.append(x)
            v.append(y)
            w.append(z)
    coordinates = np.column_stack((u, v, w))

    # Report number of coordinates in current region
    count = np.size(coordinates, axis=0)

    return coordinates, count


def prune(threshold, regions, cloud):
    """Discard quadrants with subquadrants"""

    # Create empty lists
    quadrants = []
    coordinates = []

    # Loop through points by quadrant
    for region, xyz in zip(regions, cloud):
        # Report point count in each quadrant
        count = np.size(xyz, axis=0)

        # Save regions
        if count > 0 and count < threshold:
            quadrants.append(region)
            coordinates.append(xyz)

        # Discard regions
        else:
            gs.run_command(
                "g.remove", type="region", name=region, flags="f", superquiet=True
            )

    return quadrants, coordinates


def clean(temporary):
    """
    Remove temporary maps
    """

    # Remove temporary maps
    try:
        gs.run_command(
            "g.remove",
            type=["raster", "region"],
            name=[temporary],
            flags="f",
            superquiet=True,
        )
    except:
        pass


def convert_raster(raster):
    """
    Convert raster to coordinates
    """

    # Parse raster
    data = gs.parse_command("r.stats", input=raster, flags=["gn"])

    # Find coordinates
    coordinates = []
    for datum in data.keys():
        xyz = datum.split(" ")
        x = float(xyz[0])
        y = float(xyz[1])
        z = float(xyz[2])
        coordinate = [x, y, z]
        coordinates.append(coordinate)

    return coordinates


def convert_coordinates(coordinates, z):
    """
    Parse coordinates
    """

    # Parse input coordinates
    coordinates = coordinates.split(",")
    cx = coordinates[::2]
    cy = coordinates[1::2]
    cz = z.split(",")
    if len(cz) > 1 and len(cz) != len(cx):
        gs.warning(_("Number of z-values does not match xy-coordinates!"))

    # Convert coordinates with constant z value
    if len(cz) == 1:
        coordinates = [[float(x), float(y), float(z)] for x, y in zip(cx, cy)]

    # Convert coordinates with list of z values
    elif len(cz) > 1:
        coordinates = [[float(x), float(y), float(z)] for x, y, z in zip(cx, cy, cz)]

    return coordinates


def convert_points(points, mode, z):
    """
    Convert points to coordinates
    """

    # Create list
    coordinates = []

    # Get info
    info = gs.parse_command("v.info", map=points, flags="t")

    # Convert 2D points
    if info["map3d"] == "0":
        # Parse points
        data = gs.parse_command(
            "v.to.db",
            map=points,
            option="coor",
            separator="comma",
            flags="p",
            overwrite=True,
            superquiet=True,
        )

        # Find coordinates
        coordinates = []
        for datum in data.keys():
            xyz = datum.split(",")
            x = float(xyz[1])
            y = float(xyz[2])
            z = float(z)
            coordinate = [x, y, z]
            coordinates.append(coordinate)

    # Convert 3D points
    elif info["map3d"] == "1":
        # Parse points
        data = gs.parse_command(
            "v.to.db",
            map=points,
            option="coor",
            separator="comma",
            flags="p",
            overwrite=True,
            superquiet=True,
        )

        # Find coordinates
        coordinates = []
        for datum in data.keys():
            xyz = datum.split(",")
            x = float(xyz[1])
            y = float(xyz[2])
            z = float(xyz[3])
            coordinate = [x, y, z]
            coordinates.append(coordinate)

    return coordinates


def convert_lines(lines, z):
    """
    Convert lines to coordinates
    """

    # Get info
    info = gs.parse_command("v.info", map=lines, flags="t")

    # Convert 2D lines
    if info["map3d"] == "0":
        raster = gs.append_uuid("raster")
        temporary.append(raster)
        gs.run_command(
            "v.to.rast",
            input=lines,
            output=raster,
            use="value",
            value=z,
            overwrite=True,
            superquiet=True,
        )

    # Convert 3D lines
    elif info["map3d"] == "1":
        points = gs.append_uuid("points")
        raster = gs.append_uuid("raster")
        temporary.extend([points, raster])
        region = gs.parse_command("g.region", flags=["g"])
        nsres = float(region["nsres"])
        ewres = float(region["ewres"])
        res = math.sqrt(nsres * ewres)
        gs.run_command(
            "v.to.points",
            input=lines,
            output=points,
            dmax=res,
            overwrite=True,
            superquiet=True,
        )
        gs.run_command(
            "v.to.rast",
            input=points,
            output=raster,
            use="z",
            overwrite=True,
            superquiet=True,
        )

    return raster


def grow_region(border, region, elevation):
    """Expand region extent"""

    # Find current extent
    data = gs.parse_command("g.region", region=region, flags="g")
    n = float(data["n"])
    s = float(data["s"])
    e = float(data["e"])
    w = float(data["w"])

    # Calculate expanded extent
    n = n + border
    s = s - border
    e = e + border
    w = w - border

    # Find source region extent
    data = gs.parse_command("g.region", region=source, flags="g")
    north = float(data["n"])
    south = float(data["s"])
    east = float(data["e"])
    west = float(data["w"])

    # Limit to source region extent
    if n > north:
        n = north
    if s < south:
        s = south
    if e > east:
        e = east
    if w < west:
        w = west

    # Set expanded region
    gs.run_command("g.region", n=n, s=s, e=e, w=w, align=elevation, save=region)
    gs.run_command("g.region", region=region)


def linear(rate, i, growth, decay):
    """
    Linear function
    z =  m * x + b
    where b = 0
    z = z0 +- z
    """

    # Compose linear expression
    linear = f"{rate} * dxy_{i}"

    # Append expression for calculating growth
    growth.append(f"growth_{i} = dz_{i} + {linear}")

    # Append expression for calculating decay
    decay.append(f"decay_{i} = dz_{i} - {linear}")


def exponential(rate, i, growth, decay):
    """
    Exponential function
    z = e ** (-lambda * t)
    z = z0 * z
    """

    # Compose exponential expression
    exponential = f"exp(-{rate} * dxy_{i})"

    # Append expression for calculating growth
    growth.append(f"growth_{i} = dz_{i} * {exponential}")

    # Append expression for calculating decay
    decay.append(f"decay_{i} = dz_{i} * {exponential}")


def logistic(rate, i, growth, decay):
    """
    Generalized logistic function
    z = (e ** -x) ** a
    z = z0 * z
    """

    # Compose logistic expression
    logistic = f"exp(exp(-dxy_{i}), {rate})"

    # Append expression for calculating growth
    growth.append(f"growth_{i} = dz_{i} * {logistic}")

    # Append expression for calculating decay
    decay.append(f"decay_{i} = dz_{i} * {logistic}")


def gaussian(rate, i, growth, decay):
    """
    Gaussian distribution
    z = x ** 2 / (2 * sigma ** 2)
    z = z0 * e ** -z
    """

    # Compose Gaussian expression
    gaussian = f"exp(-dxy_{i}, 2) / (2 * exp({rate}, 2))"

    # Append expression for calculating growth
    growth.append(f"growth_{i} = dz_{i} * exp(-{gaussian})")

    # Append expression for calculating decay
    decay.append(f"decay_{i} = dz_{i} * exp(-{gaussian})")


def lorentz(rate, i, growth, decay):
    """
    Cauchy-Lorentz distribution
    z = (gamma ** 2 / (x ** 2 + gamma ** 2))
    z = z0 * z
    """

    # Compose Lorentz expression
    lorentz = f"(exp({rate}, 2) / (exp(dxy_{i}, 2) + exp({rate}, 2)))"

    # Append expression for calculating growth
    growth.append(f"growth_{i} = dz_{i} * {lorentz}")

    # Append expression for calculating decay
    decay.append(f"decay_{i} = dz_{i} * {lorentz}")


def quadratic(rate, i, growth, decay):
    """
    Quadratic function
    z = a * x ** 2 + b * x + c
    where b = c = 0
    z = z0 * e ** -z
    """

    # Compose quadratic expression
    quadratic = f"{rate:.9f} * exp(dxy_{i}, 2) * dxy_{i}"

    # Append expression for calculating growth
    growth.append(f"growth_{i} = dz_{i} * exp(-{quadratic})")

    # Append expression for calculating decay
    decay.append(f"decay_{i} = dz_{i} * exp(-{quadratic})")


def cubic(rate, i, growth, decay):
    """
    Cubic function
    z = a * x ** 3 + b * x ** 2 + c * x + d
    where b = c = d = 0
    z = z0 * e ** -z
    """

    # Compose cubic expression
    cubic = f"{rate:.9f} * exp(dxy_{i}, 3) * exp(dxy_{i}, 2) * dxy_{i}"

    # Append expression for calculating growth
    growth.append(f"growth_{i} = dz_{i} * exp(-{cubic})")

    # Append expression for calculating decay
    decay.append(f"decay_{i} = dz_{i} * exp(-{cubic})")


def earthworking(
    region,
    coordinates,
    elevation,
    flat,
    border,
    mode,
    function,
    rate,
    operation,
    earthworks,
    cut,
    fill,
    disable,
):
    """
    Model local earthworks
    """

    # Create empty lists for expressions
    dxy = []
    flats = []
    dz = []
    growth = []
    decay = []
    cut_operations = []
    fill_operations = []

    if not disable:
        # Set temporary region
        gs.run_command("g.region", region=region)

        # Grow temporary region
        grow_region(border, region, elevation)

    # Set counter
    i = 0

    # Loop through coordinates
    for x, y, z in coordinates:
        # Append expression for calculating distance
        dxy.append(
            f"dxy_{i}= sqrt(((x() - {x})* (x() - {x}))+ ((y() - {y})* (y() - {y})))"
        )

        # Append expression for calculating flats
        if flat > 0.0:
            flats.append(f"dxy_{i} = if(dxy_{i} <= {flat}, 0, dxy_{i} - {flat})")
        else:
            flats.append(f"dxy_{i} = dxy_{i}")

        # Append expression for calculating relative elevation
        if mode == "relative":
            dz.append(f"dz_{i} = {z}")

        # Append expression for calculating absolute elevation
        elif mode == "absolute":
            dz.append(f"dz_{i} = {z} - {elevation}")

        # Append expressions for linear function
        if function == "linear":
            linear(rate, i, growth, decay)

        # Append expressions for exponential function
        if function == "exponential":
            exponential(rate, i, growth, decay)

        # Append expressions for logistic function
        if function == "logistic":
            logistic(rate, i, growth, decay)

        # Append expressions for Gaussian function
        if function == "gaussian":
            gaussian(rate, i, growth, decay)

        # Append expressions for Cauchy-Lorentz function
        if function == "lorentz":
            lorentz(rate, i, growth, decay)

        # Append expressions for quadratic function
        if function == "quadratic":
            quadratic(rate, i, growth, decay)

        # Append expressions for cubic function
        if function == "cubic":
            cubic(rate, i, growth, decay)

        # Append expression for cut operation
        if operation == "cut":
            cut_operations.append(
                f"if({elevation} + growth_{i} <= {elevation},"
                f"{elevation} + growth_{i},"
                f"null())"
            )

        # Append expression for fill operation
        elif operation == "fill":
            fill_operations.append(
                f"if({elevation} + decay_{i} >= {elevation},"
                f"{elevation} + decay_{i},"
                f"null())"
            )

        # Append expression for cut-fill operation
        elif operation == "cutfill":
            # append expression for cut operation
            cut_operations.append(
                f"if({elevation} + growth_{i} <= {elevation},"
                f"{elevation} + growth_{i},"
                f"null())"
            )

            # Append expression for fill operation
            fill_operations.append(
                f"if({elevation} + decay_{i} >= {elevation},"
                f"{elevation} + decay_{i},"
                f"null())"
            )

        # Advance counter
        i = i + 1

    # Model cut operation
    if operation == "cut":
        gs.mapcalc(
            f"{cut}"
            f"= eval("
            f"{','.join(dxy)},"
            f"{','.join(flats)},"
            f"{','.join(dz)},"
            f"{','.join(growth)},"
            f"nmin("
            f"{','.join(cut_operations)}"
            f")"
            f")",
            overwrite=True,
        )

    # Model fill operation
    elif operation == "fill":
        gs.mapcalc(
            f"{fill}"
            f"= eval("
            f"{','.join(dxy)},"
            f"{','.join(flats)},"
            f"{','.join(dz)},"
            f"{','.join(decay)},"
            f"nmax("
            f"{','.join(fill_operations)}"
            f")"
            f")",
            overwrite=True,
        )

    # Model cut-fill operation
    elif operation == "cutfill":
        # Model cut
        gs.mapcalc(
            f"{cut}"
            f"= eval("
            f"{','.join(dxy)},"
            f"{','.join(flats)},"
            f"{','.join(dz)},"
            f"{','.join(growth)},"
            f"nmin("
            f"{','.join(cut_operations)}"
            f")"
            f")",
            overwrite=True,
        )

        # Model fill
        gs.mapcalc(
            f"{fill}"
            f"= eval("
            f"{','.join(dxy)},"
            f"{','.join(flats)},"
            f"{','.join(dz)},"
            f"{','.join(decay)},"
            f"nmax("
            f"{','.join(fill_operations)}"
            f")"
            f")",
            overwrite=True,
        )


def series(operation, function, cuts, fills, elevation, earthworks):
    """
    Model cumulative earthworks
    """

    # Set region
    gs.run_command("g.region", region=source)

    # Model net cut
    if operation == "cut":
        # Calculate minimum cut
        cut = gs.append_uuid("cut")
        temporary.append(cut)
        gs.run_command(
            "r.series",
            input=cuts,
            output=cut,
            method="minimum",
            flags="z",
            overwrite=True,
        )
        # Calculate net cut
        gs.mapcalc(
            f"{earthworks} = if(isnull({cut}),{elevation},{cut})", overwrite=True
        )

    # Model net fill
    elif operation == "fill":
        # Calculate maximum fill
        fill = gs.append_uuid("fill")
        temporary.append(fill)
        gs.run_command(
            "r.series",
            input=fills,
            output=fill,
            method="maximum",
            flags="z",
            overwrite=True,
        )
        # Calculate net fill
        gs.mapcalc(
            f"{earthworks}= if(isnull({fill}),{elevation},{fill})", overwrite=True
        )

    # Model net cut and fill
    elif operation == "cutfill":
        # Calculate minimum cut
        cut = gs.append_uuid("cut")
        temporary.append(cut)
        gs.run_command(
            "r.series",
            input=cuts,
            output=cut,
            method="minimum",
            flags="z",
            overwrite=True,
        )

        # Calculate maximum fill
        fill = gs.append_uuid("fill")
        temporary.append(fill)
        gs.run_command(
            "r.series",
            input=fills,
            output=fill,
            method="maximum",
            flags="z",
            overwrite=True,
        )

        if function in ("linear", "lorentz"):
            # Calculate sum of cut and fill
            cutfill = gs.append_uuid("cutfill")
            temporary.append(cutfill)
            gs.run_command(
                "r.series",
                input=[cut, fill],
                output=cutfill,
                method="sum",
                flags="z",
                overwrite=True,
            )

            # Calculate net elevation
            gs.mapcalc(
                f"{earthworks} = if(isnull({cutfill}),{elevation},{cutfill})",
                overwrite=True,
            )

        if function in ("exponential", "logistic", "gaussian", "quadratic", "cubic"):
            # Calculate net change in cut
            delta_cut = gs.append_uuid("delta_cut")
            temporary.append(delta_cut)
            gs.mapcalc(f"{delta_cut} = {elevation} - {cut}", overwrite=True)

            # Calculate net change in fill
            delta_fill = gs.append_uuid("delta_fill")
            temporary.append(delta_fill)
            gs.mapcalc(f"{delta_fill} = {fill} - {elevation}", overwrite=True)

            # Calculate net change in cut and fill
            delta_cutfill = gs.append_uuid("delta_cutfill")
            temporary.append(delta_cutfill)
            gs.mapcalc(f"{delta_cutfill} = {delta_fill} - {delta_cut}", overwrite=True)

            # Calculate net cut and fill
            cutfill = gs.append_uuid("cutfill")
            temporary.append(cutfill)
            gs.mapcalc(f"{cutfill} = {elevation} + {delta_cutfill}", overwrite=True)

            # Calculate net elevation
            gs.mapcalc(
                f"{earthworks}= if(isnull({cutfill}),{elevation},{cutfill})",
                overwrite=True,
            )


def difference(elevation, earthworks, volume):
    """
    Calculate elevation change
    """

    # Create temporary raster
    if not volume:
        volume = gs.append_uuid("volume")
        temporary.append(volume)

    # Model volumetric change
    gs.mapcalc(f"{volume} = {earthworks} - {elevation}", overwrite=True)

    # Set color gradient
    gs.run_command("r.colors", map=volume, color="viridis", superquiet=True)

    # Save history
    gs.raster_history(volume, overwrite=True)

    return volume


def print_difference(operation, volume):
    """
    Print elevation change
    """

    # Find resolution
    region = gs.parse_command("g.region", flags=["g"])
    nsres = float(region["nsres"])
    ewres = float(region["ewres"])

    # Find units
    projection = gs.parse_command("g.proj", flags=["g"])
    units = projection.get("units", "units")

    # Print net change
    if operation == "cutfill":
        univar = gs.parse_command(
            "r.univar", map=volume, separator="newline", flags="g"
        )
        net = nsres * ewres * float(univar["sum"])
        if math.isnan(net):
            net = 0
        gs.info(f"Net change: {net} cubic {units.lower()}")

    # Print fill
    if operation in {"cutfill", "fill"}:
        fill = gs.append_uuid("fill")
        temporary.append(fill)
        gs.mapcalc(f"{fill} = if({volume} > 0, {volume}, null())", overwrite=True)
        univar = gs.parse_command("r.univar", map=fill, separator="newline", flags="g")
        net = nsres * ewres * float(univar["sum"])
        if math.isnan(net):
            net = 0.0
        gs.info(f"Net fill: {net} cubic {units.lower()}")

    # Print cut
    if operation in {"cutfill", "cut"}:
        cut = gs.append_uuid("cut")
        temporary.append(cut)
        gs.mapcalc(f"{cut} = if({volume} < 0, {volume}, null())", overwrite=True)
        univar = gs.parse_command("r.univar", map=cut, separator="newline", flags="g")
        net = nsres * ewres * float(univar["sum"])
        if math.isnan(net):
            net = 0.0
        gs.info(f"Net cut: {net} cubic {units.lower()}")


def postprocess(earthworks):
    """
    Postprocessing
    """

    # Set colors
    gs.run_command("r.colors", map=earthworks, color="viridis", superquiet=True)

    # Save history
    gs.raster_history(earthworks, overwrite=True)


def main():
    """
    Model earthworks
    """

    # Get input options
    options, flags = gs.parser()
    elevation = options["elevation"]
    earthworks = options["earthworks"]
    volume = options["volume"]
    mode = options["mode"]
    operation = options["operation"]
    function = options["function"]
    raster = options["raster"]
    points = options["points"]
    lines = options["lines"]
    coordinates = options["coordinates"]
    z = options["z"]
    flat = abs(float(options["flat"]))
    linear = abs(float(options["linear"]))
    exponential = abs(float(options["exponential"]))
    logistic = abs(float(options["logistic"]))
    gaussian = abs(float(options["gaussian"]))
    lorentz = abs(float(options["lorentz"]))
    quadratic = abs(float(options["quadratic"]))
    cubic = abs(float(options["cubic"]))
    threshold = float(options["threshold"])
    border = float(options["border"])
    print_volume = flags["p"]
    disable = flags["d"]

    # Check input options
    terms = [
        "linear",
        "exponential",
        "logistic",
        "gaussian",
        "lorentz",
        "quadratic",
        "cubic",
    ]
    for term in terms:
        # Check validity
        if function == term and eval(function) <= 0:
            gs.error(
                f"{function.capitalize()} slope parameter must be greater than zero."
            )

        # Set rate of growth or decay
        elif function == term and eval(function) > 0:
            rate = eval(function)

    # Run processes
    try:
        # Convert inputs
        if raster:
            coordinates = convert_raster(raster)
        elif coordinates:
            coordinates = convert_coordinates(coordinates, z)
        elif points:
            coordinates = convert_points(points, mode, z)
        elif lines:
            raster = convert_lines(lines, z)
            coordinates = convert_raster(raster)
        else:
            gs.error(_("A raster, vector, or set of coordinates is required!"))

        # Create empty lists
        cuts = []
        fills = []
        regions = []
        cloud = []

        # Save source region
        gs.run_command("g.region", save=source, overwrite=True)
        temporary.append(source)

        # Check segmentation
        if not disable:
            # Check cells
            gregion = gs.region()
            cells = gregion["cells"]
            if cells <= 100000:
                # Disable segmentation
                disable = True
                regions.append(source)
                cloud.append(coordinates)
                gs.info("Not enough cells for quadtree segmentation.")

            # Check threshold
            elif len(coordinates) <= threshold:
                # Disable segmentation
                disable = True
                regions.append(source)
                cloud.append(coordinates)
                gs.info(
                    "Not enough coordinates for quadtree segmentation. "
                    "To enable segmentation, try increasing the threshold."
                )
            else:
                # Construct quadtree
                regions, cloud = quadtree(coordinates, threshold, regions, cloud)
                gs.info(
                    "Using quadtree segmentation for faster computation. "
                    "If artifacts occur, increase the size of the border."
                )

        # Skip segmentation
        else:
            regions.append(source)
            cloud.append(coordinates)
            gs.info(
                "Not using quadtree segmentation. "
                "If processing takes too long, try enabling segmentation."
            )

        # Iterate through quadtree
        for region, coordinates in zip(regions, cloud):
            # Create temporary rasters
            if operation == "cut":
                cut = gs.append_uuid("cut")
                fill = None
                cuts.append(cut)
                temporary.append(cut)
            elif operation == "fill":
                cut = None
                fill = gs.append_uuid("fill")
                fills.append(fill)
                temporary.append(fill)
            elif operation == "cutfill":
                cut = gs.append_uuid("cut")
                fill = gs.append_uuid("fill")
                cuts.append(cut)
                fills.append(fill)
                temporary.append(cut)
                temporary.append(fill)

            # Model earthworks
            earthworking(
                region,
                coordinates,
                elevation,
                flat,
                border,
                mode,
                function,
                rate,
                operation,
                earthworks,
                cut,
                fill,
                disable,
            )

        # Model composite earthworks
        series(operation, function, cuts, fills, elevation, earthworks)

        # Calculate volume
        if volume or print_volume:
            volume = difference(elevation, earthworks, volume)

        # Print volume
        if print_volume:
            print_difference(operation, volume)

        # Postprocessing
        postprocess(earthworks)

    # Clean up
    finally:
        temporary.extend(regions)
        atexit.register(clean, temporary)


if __name__ == "__main__":
    sys.exit(main())
