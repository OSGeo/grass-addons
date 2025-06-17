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
# % description: Earthworks
# % keyword: raster
# % keyword: terrain
# %end

# %option G_OPT_R_INPUT
# % key: elevation
# % description: Input elevation raster
# % label: Input elevation raster
# %end

# %option G_OPT_R_OUTPUT
# % key: earthworks
# % description: Output elevation raster
# % label: Output earthworks
# % answer: earthworks
# %end

# %option G_OPT_R_OUTPUT
# % key: volume
# % description: Output volumetric change raster
# % label: Output volume
# % required: no
# %end

# %option
# % key: mode
# % type: string
# % answer: absolute
# % options: relative,absolute
# % description: Earthworking mode
# % descriptions: relative;Relative to exisiting topography;absolute;At given elevation
# % required: yes
# %end

# %option
# % key: operation
# % type: string
# % answer: cutfill
# % options: cut,fill,cutfill
# % description: Earthworking operation
# % descriptions: cut;Cut into topography;fill;Fill ontop topography;cutfill;Cut and fill
# % required: yes
# %end

# %option
# % key: function
# % type: string
# % answer: linear
# % options: linear,exponential
# % description: Earthworking function
# % descriptions: linear;linear decay function;exponential;Exponential decay function
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
# % answer: 1.0
# % multiple: yes
# % guisection: Input
# %end

# %option
# % key: rate
# % type: double
# % description: Rate of decay
# % label: Rate of decay
# % answer: 0.1
# % multiple: no
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

# %option
# % key: border
# % type: double
# % description: Border for adaptive region
# % label: Border for adaptive region
# % answer: 1000
# % multiple: no
# % guisection: Input
# %end

# %flag
# % key: p
# % description: Print volume
# %end

# %flag
# % key: r
# % description: Disable adaptive region
# %end

# import libraries
import grass.script as gs
from itertools import repeat
from itertools import islice
import sys
import atexit
import math

# set global variables
temporary = []


def batched(iterable, n):
    """Batch iterable into tuples"""

    # implementation of itertools.batched
    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        yield batch


def clean(temporary):
    """
    Remove temporary maps
    """

    # remove temporary maps
    try:
        gs.run_command(
            "g.remove", type="raster", name=[temporary], flags="f", superquiet=True
        )
    except:
        pass


def convert_raster(raster):
    """
    Convert raster to coordinates
    """

    # parse raster
    data = gs.parse_command("r.stats", input=raster, flags=["gn"])

    # find coordinates
    coordinates = []
    for datum in data.keys():
        xyz = datum.split(" ")
        x = xyz[0]
        y = xyz[1]
        z = xyz[2]
        coordinate = [x, y, z]
        coordinates.append(coordinate)

    return coordinates


def convert_coordinates(coordinates, z):
    """
    Parse coordinates
    """

    # parse input coordinates
    coordinates = coordinates.split(",")
    cx = coordinates[::2]
    cy = coordinates[1::2]
    cz = z.split(",")
    if len(cz) > 1 and len(cz) != len(cx):
        gs.warning(_("Number of z-values does not match xy-coordinates!"))

    # convert coordinates with constant z value
    if len(cz) == 1:
        coordinates = [[float(x), float(y), float(z)] for x, y in zip(cx, cy)]

    # # convert coordinates with list of z values
    elif len(cz) > 1:
        coordinates = [[float(x), float(y), float(z)] for x, y, z in zip(cx, cy, cz)]

    return coordinates


def convert_points(points, mode, z):
    """
    Convert points to coordinates
    """

    # create list
    coordinates = []

    # get info
    info = gs.parse_command("v.info", map=points, flags="t")

    # convert 2D points
    if info["map3d"] == "0":
        # parse points
        data = gs.parse_command(
            "v.to.db",
            map=points,
            option="coor",
            separator="comma",
            flags="p",
            overwrite=True,
            superquiet=True,
        )

        # find coordinates
        coordinates = []
        for datum in data.keys():
            xyz = datum.split(",")
            x = float(xyz[1])
            y = float(xyz[2])
            z = float(z)
            coordinate = [x, y, z]
            coordinates.append(coordinate)

    # convert 3D points
    elif info["map3d"] == "1":
        # parse points
        data = gs.parse_command(
            "v.to.db",
            map=points,
            option="coor",
            separator="comma",
            flags="p",
            overwrite=True,
            superquiet=True,
        )

        # find coordinates
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

    # get info
    info = gs.parse_command("v.info", map=lines, flags="t")

    # convert 2D lines
    if info["map3d"] == "0":
        # convert lines to raster
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

    # convert 3D lines
    elif info["map3d"] == "1":
        # convert 3D lines to raster
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


def adaptive_region(batch, elevation, border):
    """Set a temporary region containing coordinates"""

    # find bounds of current region
    gregion = gs.region()
    north = gregion["n"]
    south = gregion["s"]
    east = gregion["e"]
    west = gregion["w"]

    # unzip coordinates
    x, y, z = zip(*batch)

    # solve bounds of adaptive region
    n = float(max(y)) + border
    s = float(min(y)) - border
    e = float(max(x)) + border
    w = float(min(x)) - border
    if n >= north:
        n = north
    if s <= south:
        s = south
    if e >= east:
        e = east
    if w <= west:
        w = west

    # set adaptive region
    gs.run_command("g.region", n=n, s=s, e=e, w=w, align=elevation)


def earthworking(
    batch_size,
    batch,
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
    nonadaptive,
):
    """
    Model local earthworks
    """

    # create empty lists for expressions
    dxy = []
    flats = []
    dz = []
    growth = []
    decay = []
    cut_operations = []
    fill_operations = []

    # set adaptive region
    if not nonadaptive:
        # set temporary region
        gs.use_temp_region()

        # fit adaptive region to coordinates in batch
        adaptive_region(batch, elevation, border)

    # loop through batch
    for i in range(batch_size):
        # parse coordinate
        x = batch[i][0]
        y = batch[i][1]
        z = batch[i][2]

        # append expression for calculating distance
        dxy.append(
            f"dxy_{i}= sqrt(((x() - {x})* (x() - {x}))+ ((y() - {y})* (y() - {y})))"
        )

        # append expression for calculating flats
        if flat > 0.0:
            flats.append(f"dxy_{i} = if(dxy_{i} <= {flat}, 0, dxy_{i} - {flat})")
        else:
            flats.append(f"dxy_{i} = dxy_{i}")

        # append expression for calculating relative elevation
        if mode == "relative":
            dz.append(f"dz_{i} = {z}")

        # append expression for calculating absolute elevation
        elif mode == "absolute":
            dz.append(f"dz_{i} = {z} - {elevation}")

        # append expressions for linear function
        if function == "linear":
            # z = C - r * t

            # append expression for calculating growth
            growth.append(f"growth_{i} = dz_{i} - (-{rate}) * dxy_{i}")

            # append expression for calculating decay
            decay.append(f"decay_{i} = dz_{i} - {rate} * dxy_{i}")

        # append expression for exponential function
        elif function == "exponential":
            # z = z0 * e^(-lamba * t)

            # append expression for calculating growth
            growth.append(f"growth_{i} = dz_{i} * exp({math.e}, (-{rate} * dxy_{i}))")

            # append expression for calculating decay
            decay.append(f"decay_{i} = dz_{i} * exp({math.e}, (-{rate} * dxy_{i}))")

        # append expression for cut operation
        if operation == "cut":
            cut_operations.append(
                f"if({elevation} + growth_{i} <= {elevation},"
                f"{elevation} + growth_{i},"
                f"null())"
            )

        # append expression for fill operation
        elif operation == "fill":
            fill_operations.append(
                f"if({elevation} + decay_{i} >= {elevation},"
                f"{elevation} + decay_{i},"
                f"null())"
            )

        # append expression for cut-fill operation
        elif operation == "cutfill":
            # append expression for cut operation
            cut_operations.append(
                f"if({elevation} + growth_{i} <= {elevation},"
                f"{elevation} + growth_{i},"
                f"null())"
            )

            # append expression for fill operation
            fill_operations.append(
                f"if({elevation} + decay_{i} >= {elevation},"
                f"{elevation} + decay_{i},"
                f"null())"
            )

    # model cut operation
    if operation == "cut":
        # model earthworks
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

    # model fill operation
    elif operation == "fill":
        # model earthworks
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

    # model cut-fill operation
    elif operation == "cutfill":
        # model cut
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

        # model fill
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

    # delete temporary region
    if not nonadaptive:
        gs.del_temp_region()


def series(operation, cuts, fills, elevation, earthworks):
    """
    Model cumulative earthworks
    """

    # model net cut
    if operation == "cut":
        # calculate minimum cut
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
        # calculate net cut
        gs.mapcalc(f"{earthworks}= if(isnull({cut}),{elevation},{cut})", overwrite=True)

    # model net fill
    elif operation == "fill":
        # calculate maximum fill
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
        # calculate net fill
        gs.mapcalc(
            f"{earthworks}= if(isnull({fill}),{elevation},{fill})", overwrite=True
        )

    # model net cut and fill
    elif operation == "cutfill":
        # calculate minimum cut
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

        # calculate maximum fill
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

        # calculate sum of cut and fill
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

        # calculate net cut and fill
        gs.mapcalc(
            f"{earthworks}= if(isnull({cutfill}),{elevation},{cutfill})", overwrite=True
        )


def difference(elevation, earthworks, volume):
    """
    Calculate elevation change
    """

    # create temporary raster
    if not volume:
        volume = gs.append_uuid("volume")
        temporary.append(volume)

    # model earthworks
    gs.mapcalc(f"{volume} = {earthworks} - {elevation}", overwrite=True)

    # set color gradient
    gs.run_command("r.colors", map=volume, color="viridis", superquiet=True)

    # save history
    gs.raster_history(volume, overwrite=True)

    return volume


def print_difference(operation, volume):
    """
    Print elevation change
    """

    # find resolution
    region = gs.parse_command("g.region", flags=["g"])
    nsres = float(region["nsres"])
    ewres = float(region["ewres"])

    # find units
    projection = gs.parse_command("g.proj", flags=["g"])
    units = projection.get("units", "units")

    # print net change
    if operation == "cutfill":
        univar = gs.parse_command(
            "r.univar", map=volume, separator="newline", flags="g"
        )
        net = nsres * ewres * float(univar["sum"])
        if math.isnan(net):
            net = 0
        gs.info(f"Net change: {net} cubic {units.lower()}")

    # print fill
    if operation in {"cutfill", "fill"}:
        fill = gs.append_uuid("fill")
        temporary.append(fill)
        gs.mapcalc(f"{fill} = if({volume} > 0, {volume}, null())", overwrite=True)
        univar = gs.parse_command("r.univar", map=fill, separator="newline", flags="g")
        net = nsres * ewres * float(univar["sum"])
        if math.isnan(net):
            net = 0.0
        gs.info(f"Net fill: {net} cubic {units.lower()}")

    # print cut
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

    # set colors
    gs.run_command("r.colors", map=earthworks, color="viridis", superquiet=True)

    # save history
    gs.raster_history(earthworks, overwrite=True)


def main():
    """
    Model earthworks
    """

    # get input options
    options, flags = gs.parser()
    elevation = options["elevation"]
    earthworks = options["earthworks"]
    volume = options["volume"]
    mode = options["mode"]
    operation = options["operation"]
    function = options["function"]
    rate = abs(float(options["rate"]))
    raster = options["raster"]
    points = options["points"]
    lines = options["lines"]
    coordinates = options["coordinates"]
    z = options["z"]
    flat = float(options["flat"])
    border = float(options["border"])
    print_volume = flags["p"]
    nonadaptive = flags["r"]

    # toggle adaptive region based on region size
    if nonadaptive:
        gs.info(
            "Not using an adaptive region. "
            "If processing takes too long, try using an adaptive region."
        )
    if not nonadaptive:
        gregion = gs.region()
        cells = gregion["cells"]
        if cells <= 100000:
            nonadaptive = True
            gs.info(
                "Not using an adaptive region since there are less than 100K cells."
            )
        else:
            gs.info(
                "Using an adaptive region for faster computation. "
                "If artifacts occur, increase the size of the border."
            )

    # run processes
    try:
        # convert inputs
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

        # create empty lists
        cuts = []
        fills = []

        # batch process coordinates
        batch_size = 128
        coordinates = sorted(coordinates)
        batches = list(batched(coordinates, batch_size))
        for batch in batches:
            # set current batch size
            batch_size = len(batch)

            # create temporary rasters
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

            # model earthworks
            earthworking(
                batch_size,
                batch,
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
                nonadaptive,
            )

        # model composite earthworks
        series(operation, cuts, fills, elevation, earthworks)

        # calculate volume
        if volume or print_volume:
            volume = difference(elevation, earthworks, volume)

        # print volume
        if print_volume:
            print_difference(operation, volume)

        # postprocessing
        postprocess(earthworks)

    # clean up
    finally:
        atexit.register(clean, temporary)


if __name__ == "__main__":
    sys.exit(main())
