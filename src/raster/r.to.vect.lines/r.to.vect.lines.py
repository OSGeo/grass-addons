#!/usr/bin/env python
############################################################################
#
# MODULE:       r.to.vect.lines
# AUTHOR(S):    Hamish Bowman, Dunedin, New Zealand
# PURPOSE:      Extracts wiggle lines from raster data for use with e.g. NVIZ
# COPYRIGHT:    (C) 2012 by Hamish Bowman, and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################
#
# To make a wiggle line plot in NVIZ:
#   g.region raster=elevation.dem
#   r.to.vect.lines.py in=elevation.dem out=wiggle_lines
#   eval `v.info -g wiggle_lines`
#   r.mapcalc "floor = $bottom"
#   nviz elev=floor vector=wiggle_lines
#

# %module
# % description: Convert raster rows to vector lines.
# % keyword: raster
# % keyword: conversion
# % keyword: wiggles
# %end
# %option
# % key: input
# % type: string
# % key_desc: name
# % gisprompt: old,cell,raster
# % required: yes
# % description: Name of input raster map
# %end
# %option
# % key: output
# % type: string
# % key_desc: name
# % gisprompt: new,vector,vector
# % required: yes
# % description: Name for output vector map
# %end
# %option
# % key: skip
# % type: integer
# % required: no
# % description: Sample every Nth grid row
# % answer: 10
# % options: 1-100000
# %end
# %flag
# % key: v
# % description: Sample vertically (default is to sample horizontally)
# %end

import os
import sys
from grass.script import core as grass
from grass.lib.gis import *
from grass.lib.vector import *
from grass.lib.raster import *
from ctypes import *

# check if GRASS is running or not
if "GISBASE" not in os.environ:
    sys.exit("You must be in GRASS GIS to run this program")


def main():
    G_gisinit(sys.argv[0])

    inmap = options["input"]
    outmap = options["output"]
    skip = int(options["skip"])
    go_vert = flags["v"]

    if go_vert:
        sys.exit("Vertical lines are yet to do.")

    ##### Query the region
    region = Cell_head()
    G_get_window(byref(region))

    #### Raster map setup
    # find raster map in search path
    mapset = None
    if "@" in inmap:
        inmap, mapset = inmap.split("@")

    gfile = grass.find_file(name=inmap, element="cell", mapset=mapset)
    if not gfile["name"]:
        grass.fatal(_("Raster map <%s> not found") % inmap)

    # determine the inputmap type (CELL/FCELL/DCELL)
    data_type = Rast_map_type(inmap, mapset)

    if data_type == CELL_TYPE:
        ptype = POINTER(c_int)
        type_name = "CELL"
    elif data_type == FCELL_TYPE:
        ptype = POINTER(c_float)
        type_name = "FCELL"
    elif data_type == DCELL_TYPE:
        ptype = POINTER(c_double)
        type_name = "DCELL"

    # print "Raster map <%s> contains data type %s." % (inmap, type_name)

    in_fd = Rast_open_old(inmap, mapset)
    in_rast = Rast_allocate_buf(data_type)
    in_rast = cast(c_void_p(in_rast), ptype)

    rows = Rast_window_rows()
    cols = Rast_window_cols()
    # print "Current region is %d rows x %d columns" % (rows, cols)

    #### Vector map setup
    # define map structure
    map_info = pointer(Map_info())

    # define open level (level 2: topology)
    Vect_set_open_level(2)

    # open new 3D vector map
    Vect_open_new(map_info, outmap, True)
    print("ddd")
    Vect_hist_command(map_info)

    # Create and initialize structs to store points/lines and category numbers
    Points = Vect_new_line_struct()
    Cats = Vect_new_cats_struct()
    fea_type = GV_LINE

    LineArrayType = c_double * cols
    xL = LineArrayType()
    yL = LineArrayType()
    zL = LineArrayType()

    #### iterate through map rows
    for row in range(rows):
        if row % skip != 0:
            continue

        # read a row of raster data into memory, then print it
        Rast_get_row(in_fd, in_rast, row, data_type)
        # print row, in_rast[0:cols]
        # print row, in_rast[0:5]

        # y-value
        coor_row_static = Rast_row_to_northing((row + 0.5), byref(region))
        # x-end nodes
        # coor_col_min = G_col_to_easting((0 + 0.5), byref(region))
        # coor_col_max = G_col_to_easting((cols - 0.5), byref(region))
        # print '  ',coor_row_static,coor_col_min,coor_col_max

        # reset
        n = 0
        for col in range(cols):
            xL[col] = yL[col] = zL[col] = 0

        # TODO check for NULL
        for col in range(cols):
            #            if not G_is_null_value(byref(in_rast[col]), data_type):
            if in_rast[col] > -2e9:
                xL[n] = Rast_col_to_easting((col + 0.5), byref(region))
                yL[n] = coor_row_static
                zL[n] = in_rast[col]
                n = n + 1

        # print valid_cols,n
        Vect_cat_del(Cats, 1)
        # beware if you care, this creates a cat 0
        Vect_cat_set(Cats, 1, row)
        Vect_reset_line(Points)
        Vect_copy_xyz_to_pnts(Points, xL, yL, zL, n)
        Vect_write_line(map_info, fea_type, Points, Cats)

    # Build topology for vector map and close them all
    Vect_build(map_info)
    Vect_close(map_info)
    Rast_close(in_fd)
    G_done_msg("")


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
