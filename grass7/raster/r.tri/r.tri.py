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
# COPYRIGHT:    (C) 2015-2020 Steven Pawley and by the GRASS Development Team
#
###############################################################################

#%module
#% description: Computes the Terrain Ruggedness Index.
#%end

#%option G_OPT_R_INPUT
#% description: Input elevation raster
#% key: input
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Output Terrain Ruggedness Index (TRI)
#% key: output
#% required: yes
#%end

#%option
#% key: size
#% type: integer
#% description: Size of neighbourhood in cells
#% required: yes
#% answer: 3
#%end

#%option
#% key: n_jobs
#% type: integer
#% label: Number of processing cores for tiled calculation
#% description: Number of processing cores for tiled calculation (negative numbers are all cpus -1, -2 etc.)
#% required: no
#% answer: 1
#%end

#%flag
#% key: c
#% description: Use circular neighborhood
#%end

import atexit
import math
import random
import string
import sys

import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import raster as gr

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


def tile_shape(region, n_jobs):
    """Calculates the number of tiles required for one tile per cpu

    Parameters
    ----------
    region : pygrass.gis.region.Region
        The computational region object.
    
    n_jobs : int
        The number of processing cores.
    
    Returns
    -------
    width, height : tuple
        The width and height of each tile.
    """
    n = math.sqrt(n_jobs)
    width = int(math.ceil(region.cols / n))
    height = int(math.ceil(region.rows / n))

    return width, height


def main():
    dem = options["input"]
    tri = options["output"]
    size = int(options["size"])
    n_jobs = int(options["n_jobs"])
    circular = flags["c"]
    radius = int((size - 1) / 2)

    region = Region()

    # Some checks
    if "@" in tri:
        tri = tri.split("@")[0]

    if n_jobs == 0:
        gs.fatal("Number of processing cores for parallel computation must not equal 0")

    if n_jobs < 0:
        system_cores = mp.cpu_count()
        n_jobs = system_cores + n_jobs + 1

    if n_jobs > 1:
        if gs.find_program("r.mapcalc.tiled") is False:
            gs.fatal(
                "The GRASS addon r.mapcalc.tiled must also be installed if n_jobs != 1. Run 'g.extension r.mapcalc.tiled'"
            )

    # Calculate TRI based on map calc statements
    gs.message("Calculating the Topographic Ruggedness Index...")

    # Generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the center cell
    offsets = focal_expr(radius=radius, window_square=not circular)
    terms = []
    for d in offsets:
        d_str = ",".join(map(str, d))
        terms.append("({dem}[{d}]-{dem})^2".format(dem=dem, d=d_str))

    # Define the calculation expression
    ncells = len(offsets) + 1
    terms = " + ".join(terms)

    # Perform the r.mapcalc calculation with the moving window
    expr = "{tri} = float(sqrt(({terms}) / {ncells}))".format(
        tri=tri, ncells=ncells, terms=terms
    )

    width, height = tile_shape(region, n_jobs)

    if width < region.cols and height < region.rows and n_jobs > 1:
        gr.mapcalc_tiled(
            expression=expr,
            width=width,
            height=height,
            processes=n_jobs,
            overlap=int((size + 1) / 2),
            output=tri,
        )
    else:
        gs.mapcalc(expr)

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
