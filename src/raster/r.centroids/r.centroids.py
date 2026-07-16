#!/usr/bin/env python


############################################################################
#
# MODULE:    r.centroids
#
# AUTHOR(S): Caitlin Haedrich (caitlin dot haedrich gmail com)
#
# PURPOSE:   Wrapper for r.volume. Creates vector map of centroids from a
#            raster of "clumps"; r.clumps creates "clumps" of data.
#
# SPDX-FileCopyrightText: 2021 Caitlin Haedrich
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
#############################################################################

# %module
# % description: Creates vector map of centroids from raster of "clumps".
# % keyword: raster
# % keyword: centroid
# % keyword: clumps
# % keyword: vector
# % keyword: centerpoint
# %end

# %option G_OPT_R_INPUT
# % description: Raster map of clumps, clusters of same-valued pixels
# %end

# %option G_OPT_V_OUTPUT
# %end

import grass.script as gs
import sys


def main():
    options, flags = gs.parser()

    # options and flags into variables
    in_raster = options["input"]
    out_vector = options["output"]
    gs.run_command(
        "r.volume",
        quiet=True,
        input=in_raster,
        clump=in_raster,
        centroids=out_vector,
        errors="exit",
    )
    gs.run_command(
        "v.db.dropcolumn", map=out_vector, columns=["volume", "sum", "count", "average"]
    )


if __name__ == "__main__":
    sys.exit(main())

