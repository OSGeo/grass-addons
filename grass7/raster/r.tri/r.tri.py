#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       Terrain Ruggedness Index
#
# AUTHOR(S):    Steven Pawley
#
# PURPOSE:      Simple script to calculate the Terrain Ruggedness Index (TRI)
#               of Riley et al. (1999)
#
# COPYRIGHT:    (C) 2015 Steven Pawley and by the GRASS Development Team
#
###############################################################################

#%module
#% description: Terrain Ruggedness Index
#%end

#%option G_OPT_R_INPUT
#% description: Input elevation raster
#% key: input
#% required : yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Output Terrain Ruggedness Index (TRI)
#% key: output
#% required : yes
#%end

#%option
#% key: size
#% type: integer
#% description: Size of neighbourhood in cells
#% answer: 3
#% guisection: Required
#%end

#%option
#% key: n_jobs
#% type: integer
#% description: Number of processes cores for computation
#% required: no
#% answer: 1
#% end

#%flag
#% key: c
#% description: Use circular neighborhood
#%end

import sys
import atexit
import random
import string
import multiprocessing as mp
import math
import grass.script as gs
import grass.script.core as gcore
from grass.pygrass.modules.shortcuts import raster as grast
from grass.pygrass.gis.region import Region

TMP_RAST = []


def cleanup():
    gs.message("Deleting intermediate files...")

    for f in TMP_RAST:
        gs.run_command("g.remove", type="raster", name=f, flags="f", quiet=True)


def temp_map(name):
    tmp = name + "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(4)]
    )
    TMP_RAST.append(tmp)

    return tmp


def focal_expr(radius, window_square=False):
    """Returns array offsets relative to centre pixel (0,0) for a matrix of
    size radius

    Args
    ----
    radius : int
        Radius of the focal function
    window_square : bool. Optional (default is False)
        Boolean to use a circular or square window

    Returns
    -------
    offsets : list
        List of pixel positions (row, col) relative to the center pixel
        ( 1, -1)  ( 1, 0)  ( 1, 1)
        ( 0, -1)  ( 0, 0)  ( 0, 1)
        (-1, -1)  (-1, 0)  (-1, 1)"""

    offsets = []

    # generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the centre cell
    if window_square:

        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                if (i, j) != (0, 0):
                    offsets.append((i, j))

    else:

        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                row = i + radius
                col = j + radius

                if pow(row - radius, 2) + pow(col - radius, 2) <= pow(radius, 2) and (
                    i,
                    j,
                ) != (0, 0):
                    offsets.append((j, i))

    return offsets


def main():
    dem = options["input"]
    tri = options["output"]
    size = int(options["size"])
    n_jobs = int(options["n_jobs"])
    circular = flags["c"]

    radius = int((size - 1) / 2)

    if n_jobs != 1:
        if not gcore.find_program("r.mapcalc.tiled", "--help"):
            msg = "Parallelized computation requires the extension 'r.mapcalc.tiled' to be installed."
            msg = " ".join([msg, "Install it using 'g.extension r.mapcalc.tiled'"])
            gs.fatal(msg)

        if n_jobs == 0:
            gs.fatal(
                "Number of processing cores for parallel computation must not equal 0"
            )

        if n_jobs < 0:
            system_cores = mp.cpu_count()
            n_jobs = system_cores + n_jobs + 1

    # calculate TRI based on map calc statements
    gs.message("Calculating the Topographic Ruggedness Index...")

    # generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the center cell
    offsets = focal_expr(radius=radius, window_square=not circular)
    terms = []
    for d in offsets:
        valid = ",".join(map(str, d))
        invalid = ",".join([str(-d[0]), str(-d[1])])
        terms.append(
            "if(isnull({dem}[{d}]), if(isnull({dem}[{e}]), (median({dem})-{dem})^2, ({dem}[{e}]-{dem}^2)), ({dem}[{d}]-{dem})^2)".format(
                dem=dem, d=valid, e=invalid
            )
        )

    # define the calculation expression
    ncells = len(offsets) + 1
    terms = " + ".join(terms)

    # expr = "$tri = sqrt((%s" % " + ".join(terms) + ") / $ncells)"

    expr = "{tri} = sqrt(({terms}) / {ncells})".format(
        tri=tri, ncells=ncells, terms=terms
    )

    # perform the r.mapcalc calculation with the moving window
    if n_jobs == 1:
        gs.mapcalc(expr, tri=tri, dem=dem, ncells=ncells)
    else:
        reg = Region()
        width = math.ceil(reg.cols / n_jobs)
        height = math.ceil(reg.rows / n_jobs)
        grast.mapcalc_tiled(expr, width=width, height=height, processes=n_jobs, overlap=radius)

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
