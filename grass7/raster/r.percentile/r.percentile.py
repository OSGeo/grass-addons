#!/usr/bin/env python
# -*- coding: utf-8

"""
MODULE:    r.percentile

AUTHOR(S): Steven Pawley <dr.stevenpawley@gmail.com>

PURPOSE:   Calculates the ratio of cells in a neighborhood that are lower in 
           elevation than the centre cell in a

COPYRIGHT: (C) 2020 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

#%Module
#% description: Calculation of elevation percentile
#% keyword: raster
#% keyword: terrain
#%end

#%option G_OPT_R_ELEV
#% key: input
#% description: Name of elevation raster map
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% description: Name of output elevation percentile raster map
#% required: yes
#%end

#%option
#% key: size
#% type: integer
#% description: Size of the neighborhood (odd number, valid range 3-101)
#% required: no
#% answer: 3
#% end

#%option
#% key: n_jobs
#% type: integer
#% description: Number of processes cores for computation
#% required: no
#% answer: 1
#% end

#%flag
#% key: s
#% description: Use square moving window instead of circular moving window
#%end

import sys
import math
import multiprocessing as mp

import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r


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


def focal_expr(radius, window_square=False):
    """Returns array offsets relative to centre pixel (0,0) for a matrix of
    size radius

    Parameters
    ----------
    radius : int
        The radius of the focal function.

    window_square : bool (opt). Default is False
        Whether to use a circular or square focal window.

    Returns
    -------
    offsets : list
        List of pixel positions (row, col) relative to the center pixel
        ( 1, -1)  ( 1, 0)  ( 1, 1)
        ( 0, -1)  ( 0, 0)  ( 0, 1)
        (-1, -1)  (-1, 0)  (-1, 1)
    """
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


def elevation_percentile(input, output, radius=3, window_square=False, n_jobs=1):
    """Calculates the percentile which is the ratio of the number of points of lower
    elevation to the total number of points in the surrounding region

    Notes
    -----
    Note this function is currently a bottle-neck of the module because r.mapcalc
    becomes slow with large statements. Ideally, a C module that calculates
    elevation percentile is required.

    Parameters
    ----------
    input : str
        The GRASS raster map (elevation) to perform calculation on.

    radius : int
        The neighborhood radius (in pixels).

    window_square : bool (opt). Default is False
        Whether to use a square or circular neighborhood.

    n_jobs : int
        The number of processing cores for parallel computation.

    Returns
    -------
    PCTL : str
        Name of the raster map with elevation percentile for processing step L
    """
    # get offsets for given neighborhood radius
    offsets = focal_expr(radius=radius, window_square=window_square)

    # generate grass mapcalc terms and execute
    n_pixels = float(len(offsets))

    # create mapcalc expr
    # if pixel in neighborhood contains nodata, attempt to use opposite neighbor
    # if opposite neighbor is also nodata, then use center pixel
    terms = []
    for d in offsets:
        valid = ",".join(map(str, d))
        terms.append("if({input}[{d}]<={input})".format(input=input, d=valid))

    expr = "{x} = ({terms}) / {n}".format(x=output, terms=" + ".join(terms), n=n_pixels)

    region = Region()
    width, height = tile_shape(region, n_jobs)

    if n_jobs > 1:
        r.mapcalc_tiled(
            expression=expr,
            width=width,
            height=height,
            processes=n_jobs,
            overlap=radius+1,
            output=output,
        )
    else:
        gs.mapcalc(expr)


def main():
    elev = options["input"]
    output = options["output"].split("@")[0]
    moving_window_square = flags["s"]
    size = int(options["size"])
    n_jobs = int(options["n_jobs"])

    # Some checks ---------------------------------------------------------------------
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

    # Elevation percentile
    elevation_percentile(
        input=elev,
        output=output,
        radius=int((size - 1) / 2),
        window_square=moving_window_square,
        n_jobs=n_jobs,
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
