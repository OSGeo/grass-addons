#!/usr/bin/env python

############################################################################
#
# MODULE:       v.what.spoly
# AUTHOR(S):    Alexander Muriy
#               (Institute of Environmental Geoscience, Moscow, Russia)
#               e-mail: amuriy AT gmail DOT com
#
# PURPOSE:      Queries vector map with overlaping "spaghetti" polygons (e.g. Landsat footprints) at given location
#
# COPYRIGHT:    (C) 2016 Alexander Muriy / GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################
# %Module
# %  description: Queries vector map with overlaping "spaghetti" polygons (e.g. Landsat footprints) at given location. Polygons must have not intersected boundaries.
# %  keyword: vector
# %  keyword: topology
# %End
# %Option
# %  key: input
# %  type: string
# %  required: yes
# %  multiple: no
# %  key_desc: name
# %  description: Name of input polygon vector map
# %  gisprompt: old,vector,vector
# %End
# %Option
# %  key: output
# %  type: string
# %  required: no
# %  multiple: no
# %  key_desc: name
# %  description: Name of output vector map
# %  gisprompt: new,vector,vector
# %End
# %Option
# %  key: coor
# %  type: string
# %  required: yes
# %  multiple: no
# %  key_desc: name
# %  description: Coordinates to query
# %End
# %Flag
# %  key: p
# %  description: Only print selected polygons
# %End
############################################################################

import sys
import os
import glob
import atexit

import grass.script as grass
from grass.script import core as grass

try:
    from osgeo import ogr
except:
    print("Please install GDAL-Python bindings or add them to PYTHONPATH")
    sys.exit(1)


def cleanup():
    inmap = options["input"]
    grass.try_remove(tmp)
    for f in glob.glob(tmp + "*"):
        grass.try_remove(f)
    with open(os.devnull, "w") as nuldev:
        grass.run_command(
            "g.remove",
            type_="vect",
            pat="v_temp*",
            flags="f",
            quiet=True,
            stderr=nuldev,
        )


def main():
    inmap = options["input"]
    outmap = options["output"]
    coor = options["coor"]
    coor = coor.replace(",", " ")

    global tmp, grass_version

    # setup temporary files
    tmp = grass.tempfile()

    # check for LatLong location
    if grass.locn_is_latlong():
        grass.fatal("Module works only in locations with cartesian coordinate system")

    # check if input file exists
    if not grass.find_file(inmap, element="vector")["file"]:
        grass.fatal(_("<%s> does not exist.") % inmap)

    ## DO IT ##
    ## add categories to boundaries
    grass.run_command(
        "v.category",
        input_=inmap,
        option="add",
        type_="boundary",
        output="v_temp_bcats",
        quiet=True,
        stderr=None,
    )

    ## export polygons to CSV + WKT
    tmp1 = tmp + ".csv"
    tmp2 = tmp + "2.csv"
    grass.run_command(
        "v.out.ogr",
        input_="v_temp_bcats",
        output=tmp1,
        format_="CSV",
        type_=("boundary"),
        lco="GEOMETRY=AS_WKT",
        quiet=True,
        stderr=None,
    )

    ## convert lines to polygons
    f1 = open(tmp1, "r")
    f2 = open(tmp2, "w")
    for line in f1:
        f2.write(
            line.replace("LINESTRING", "POLYGON")
            .replace(" (", " ((")
            .replace(')"', '))"')
        )
    f1.close()
    f2.close()

    with open(tmp2, "r") as f:
        print(f.read())

    ## open CSV with OGR and get layer name
    f = ogr.Open(tmp2, 0)
    lyr = f.GetLayer(0)
    lyr_name = lyr.GetName()

    ## make spatial query with coordinates
    coords = "%s %s" % (coor, coor)
    tmp3 = tmp + "_v_temp_select.shp"
    cmd = "ogr2ogr " + " -spat " + coords + " " + tmp3 + " " + tmp2 + " " + lyr_name
    os.system(cmd)

    ## open SHP with OGR and get layer name
    f = ogr.Open(tmp3, 0)
    lyr = f.GetLayer(0)
    lyr_name = lyr.GetName()

    ## print selected objects to stdout or write into vector map
    if flags["p"]:
        cmd = "ogrinfo -al -fields=YES -geom=SUMMARY" + " " + tmp3 + " " + lyr_name
        os.system(cmd)
    else:
        grass.run_command(
            "v.in.ogr",
            input_=tmp3,
            layer=lyr_name,
            output=outmap,
            flags="c",
            quiet=True,
            stderr=None,
        )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
