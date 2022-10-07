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

# %module
# % description: Computes the Terrain Ruggedness Index.
# % keyword: raster
# % keyword: surface
# % keyword: terrain
# % keyword: ruggedness
# % keyword: parallel
# %end

# %option G_OPT_R_INPUT
# % description: Input elevation raster
# % key: input
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % description: Output Terrain Ruggedness Index (TRI)
# % key: output
# % required: yes
# %end

# %option
# % key: size
# % type: integer
# % description: Size of neighbourhood in cells (> 2 and <= 51)
# % required: yes
# % answer: 3
# %end

# %option
# % key: exponent
# % type: double
# % description: Distance weighting exponent (>= 0 and <= 4.0)
# % required: no
# % answer: 0.0
# %end

# %option
# % key: processes
# % type: integer
# % label: Number of processing cores for tiled calculation
# % description: Number of processing cores for tiled calculation (negative numbers are all cpus -1, -2 etc.)
# % required: no
# % answer: 1
# %end

# %flag
# % key: c
# % description: Use circular neighborhood
# %end

import math
import multiprocessing as mp
import sys

import grass.script as gs
import numpy as np
from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import raster as gr


def focal_expr(radius, circular=False):
    """Returns array offsets relative to centre pixel (0,0) for a matrix of
    size radius

    Args
    ----
    radius : int
        Radius of the focal function
    circular : bool. Optional (default is False)
        Boolean to use a circular or square window

    Returns
    -------
    offsets : list
        List of pixel positions (row, col) relative to the center pixel
        ( 1, -1)  ( 1, 0)  ( 1, 1)
        ( 0, -1)  ( 0, 0)  ( 0, 1)
        (-1, -1)  (-1, 0)  (-1, 1)
    """

    # generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the centre cell
    size = radius * 2 + 1
    centre = int(size / 2)

    rows, cols = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    row_offsets, col_offsets = np.meshgrid(rows, cols)

    # create circular mask (also masking centre)
    if circular:
        mask = distance_from_centre(radius) <= radius
    else:
        mask = np.ones((size, size), dtype=np.bool)
    mask[centre, centre] = False

    # mask and flatten the offsets
    row_offsets = row_offsets[mask]
    col_offsets = col_offsets[mask]

    # create a list of offsets
    offsets = list()
    for i, j in zip(row_offsets, col_offsets):
        offsets.append((i, j))

    return offsets


def distance_from_centre(radius):
    """Create a square matrix filled with the euclidean distance from the
    centre cell

    Parameters
    ----------
    radius : int
        Radius of the square matrix in cells.

    Returns
    -------
    dist_from_centre : 2d ndarray
        Square matrix with each cell filled with the distance from the centre
        cell.

    """
    size = radius * 2 + 1
    centre = int(size / 2)

    Y, X = np.ogrid[:size, :size]
    dist_from_centre = np.sqrt((X - centre) ** 2 + (Y - centre) ** 2)

    return dist_from_centre


def idw_weights(radius, p, circular=False):
    """Create square matrix of inverse distance weights

    The weights are normalized (sum to 1) and are flattened as a list

    Parameters
    ----------
    radius : int
        Radius of the square matrix in cells.

    p : float
        Distance weighting power. p=0 gives equal weights.

    circular : bool (opt). Default is False
        Optionally use a circular mask.

    Returns
    -------
    W : list
        Returns a square matrix of weights that excludes the centre cell, or
        other cells if a circular mask is used. The matrix is flattened and
        returned as a list.
    """
    size = radius * 2 + 1
    centre = int(size / 2)

    # create distance matrix
    dist = distance_from_centre(radius)

    # create inverse distance weights
    W = dist.copy()
    W[centre, centre] = np.inf
    W = 1 / (W**p)

    # normalize weights to sum to 1 (excluding centre)
    W[centre, centre] = np.inf
    W = W / W[np.isfinite(W)].sum()

    # circular mask
    if circular:
        mask = dist <= radius
    else:
        mask = np.isfinite(W)
    mask[centre, centre] = False

    return list(W[mask])


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
    exponent = float(options["exponent"])
    processes = int(options["processes"])
    circular = flags["c"]
    radius = int((size - 1) / 2)

    region = Region()

    # Some checks
    if "@" in tri:
        tri = tri.split("@")[0]

    if processes == 0:
        gs.fatal("Number of processing cores for parallel computation must not equal 0")

    if processes < 0:
        system_cores = mp.cpu_count()
        processes = system_cores + processes + 1

    if processes > 1:
        if gs.find_program("r.mapcalc.tiled") is False:
            gs.fatal(
                "The GRASS addon r.mapcalc.tiled must also be installed if n_jobs != 1. Run 'g.extension r.mapcalc.tiled'"
            )

    if size <= 2 or size > 51:
        gs.fatal("size must be > 2 and <= 51")

    if size % 2 != 1:
        gs.fatal("size must be an odd number")

    if exponent < 0 or exponent > 4.0:
        gs.fatal("exponent must be >= 0 and <= 4.0")

    # Calculate TRI based on map calc statements
    gs.message("Calculating the Topographic Ruggedness Index...")

    # Generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the center cell
    offsets = focal_expr(radius, circular)
    weights = idw_weights(radius, exponent, circular)
    terms = []
    for d, w in zip(offsets, weights):
        d_str = ",".join(map(str, d))
        terms.append("{w}*abs({dem}[{d}]-{dem})".format(dem=dem, d=d_str, w=w))

    # Define the calculation expression
    terms = "+".join(terms)

    # Perform the r.mapcalc calculation with the moving window
    expr = "{tri} = float({terms})".format(tri=tri, terms=terms)

    width, height = tile_shape(region, processes)

    if width < region.cols and height < region.rows and processes > 1:
        gr.mapcalc_tiled(
            expression=expr,
            width=width,
            height=height,
            processes=processes,
            overlap=int((size + 1) / 2),
            output=tri,
        )
    else:
        gs.mapcalc(expr)

    # update metadata
    opts = ""
    if circular:
        opts = "-c"

    gr.support(
        map=tri,
        title="Terrain Ruggedness Index",
        description="Generated with r.tri input={dem} output={tri} size={size} exponent={exponent} {flags}".format(
            dem=dem, tri=tri, size=size, exponent=exponent, flags=opts
        ),
    )

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
