#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:	    v.stats
#
# AUTHOR(S):   Pietro Zambelli (University of Trento)
#
# COPYRIGHT:	(C) 2013 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %Module
# % description: Calculates vector statistics
# % keyword: vector
# % keyword: statistics
# % keyword: shape
# % overwrite: yes
# %End
# %option G_OPT_V_MAP
# % key: vector
# % description: Name of input vector map
# % required: yes
# %end
# %option
# % key: layer
# % type: integer
# % description: Vector layer
# % multiple: no
# % required: no
# % answer: 1
# %end
# %option G_OPT_R_INPUTS
# % key: rasters
# % description: Name of input raster maps
# % multiple: yes
# % required: no
# %end
# %option G_OPT_R_INPUT
# % key: zones
# % description: Name of raster zones map
# % multiple: no
# % required: no
# %end
# %option
# % key: rprefix
# % description: Raster prefixes
# % multiple: yes
# % required: no
# %end
# %option
# % key: skipshape
# % type: string
# % multiple: yes
# % description: Skip shape columns
# % required: no
# % answer: area_id
# %end
# %option
# % key: skipunivar
# % type: string
# % multiple: yes
# % description: Skip shape columns
# % required: no
# % answer: label,all_cells,non_null_cells,null_cells,mean_of_abs,sum,sum_abs
# %end
# %option
# % key: shpcsv
# % type: string
# % multiple: no
# % description: CSV with the vector statistics of the shape
# % required: no
# %end
# %option
# % key: rstcsv
# % type: string
# % multiple: yes
# % description: CSV with the statistics of the raster maps
# % required: no
# %end
# %option
# % key: rstpercentile
# % type: integer
# % multiple: no
# % description: Raster percentile to use
# % required: no
# % answer: 90
# %end
# %option
# % key: newlayer
# % type: integer
# % description: New vector layer that will be add to the vector map
# % multiple: no
# % required: no
# % answer: 2
# %end
# %option
# % key: newlayername
# % type: string
# % description: New vector layer that will be add to the vector map
# % multiple: no
# % required: no
# %end
# %option
# % key: newtabname
# % type: string
# % description: New vector layer that will be add to the vector map
# % multiple: no
# % required: no
# %end
# %option
# % key: separator
# % type: string
# % description: New vector layer that will be add to the vector map
# % multiple: no
# % required: no
# % answer: ;
# %end
# %option
# % key: nprocs
# % type: integer
# % description: Number of process that will be used
# % multiple: no
# % required: no
# % answer: 1
# %end
# %flag
# % key: r
# % description: Read from existing CSV files
# %end
# -----------------------------------------------------
import sys
import os

from grass.script.core import parser


from grass.pygrass.utils import get_lib_path, get_mapset_raster
from grass.pygrass.vector import VectorTopo, Vector
from grass.pygrass.vector.table import Link

path = get_lib_path("v.stats", "")
if path is None:
    raise ImportError("Not able to find the path %s directory." % path)

sys.path.append(path)

from vstats import get_shp_csv, get_zones, get_rst_csv
from imp_csv import update_cols


def main(opt, flg):
    #
    # Set check variables
    #
    overwrite = True
    rasters = opt["rasters"].split(",") if opt["rasters"] else []
    rprefix = opt["rprefix"].split(",") if opt["rprefix"] else []

    def split(x):
        return x.split("@") if "@" in x else (x, "")

    vname, vmset = split(opt["vector"])
    shpcsv = opt["shpcsv"] if opt["shpcsv"] else vname + ".csv"
    rstcsv = (
        opt["rstcsv"].split(",")
        if opt["rstcsv"]
        else [split(rst)[0] + ".csv" for rst in rasters]
    )
    zones = opt["zones"] if opt["zones"] else vname + "_zones"
    nprocs = int(opt.get("nprocs", 1))
    if rasters:
        if rprefix and len(rasters) != len(rprefix):
            raise
        if len(rasters) != len(rstcsv):
            raise
        prefixes = rprefix if rprefix else rasters
    else:
        prefixes = None

    skipshp = opt["skipshape"].split(",") if opt["skipshape"] else []
    skiprst = opt["skipunivar"].split(",") if opt["skipunivar"] else []
    layer = int(opt["layer"])
    newlayer = int(opt["newlayer"])
    newlayername = opt["newlayername"] if opt["newlayername"] else vname + "_stats"
    newtabname = opt["newtabname"] if opt["newtabname"] else vname + "_stats"
    rstpercentile = float(opt["rstpercentile"])
    separator = opt.get("separator", ";")

    #
    # compute
    #
    if not os.path.exists(shpcsv):
        get_shp_csv(opt["vector"], shpcsv, overwrite, separator)
    if not get_mapset_raster(zones):
        get_zones(opt["vector"], zones, layer)
    if not rstcsv or not os.path.exists(rstcsv[0]):
        get_rst_csv(rasters, zones, rstcsv, rstpercentile, overwrite, nprocs, separator)

    newlink = Link(newlayer, newlayername, newtabname)
    newtab = newlink.table()
    with Vector(vname, vmset, mode="r", layer=layer) as vct:
        mode = "r" if newlink in vct.dblinks else "rw"

    with VectorTopo(vname, vmset, mode=mode, layer=layer) as vct:
        update_cols(
            newtab, shpcsv, rstcsv, prefixes, skipshp, skiprst, separator=separator
        )

        if mode == "rw":
            # add the new link
            vct.dblinks.add(newlink)
            vct.build()


if __name__ == "__main__":
    main(*parser())
