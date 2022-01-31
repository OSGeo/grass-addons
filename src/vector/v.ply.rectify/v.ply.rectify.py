#!/usr/bin/env python
#
############################################################################
#
# MODULE:       v.ply.rectify
#
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Import PLY point data, georeference and export them
#
# COPYRIGHT:    (c) 2012 The GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# %module
# % description: Imports PLY points, georeferences and exports them.
# % keyword: vector
# % keyword: import
# % keyword: export
# % keyword: rectify
# %end
# %option G_OPT_F_INPUT
# % description: Name of input PLY file
# %end
# %option G_OPT_V_OUTPUT
# % description: Default is input name without .ply
# % required: no
# %end
# %flag
# % key: s
# % description: Also export point cloud shifted to center
# %end

import sys
import os
import atexit
import string
import shutil
from grass.script import core as grass
from grass.script import vector as gvector


def main():

    export_shifted = flags["s"]

    currmapset = grass.gisenv()["MAPSET"]

    #### check for v.in.ply, v.out.ply
    if not grass.find_program("v.in.ply", "--help"):
        grass.fatal(
            _("The GRASS addon v.in.ply was not found, please install it first.\n")
        )
    if not grass.find_program("v.out.ply", "--help"):
        grass.fatal(
            _("The GRASS addon v.out.ply was not found, please install it first.\n")
        )

    # import input PLY file
    infile = options["input"]
    if not os.path.exists(infile):
        grass.fatal(_("Unable to read input file <%s>") % infile)
    grass.debug("input file=[%s]" % infile)

    if not infile[-4:].lower() == ".ply":
        grass.fatal(_("Input file must end with .ply or .PLY"))

    gcpfile = infile[:-4] + ".txt"
    srcdir, ply = os.path.split(infile)
    ply = ply[:-4]

    if not os.path.exists(gcpfile):
        gcpfile = infile[:-4] + ".TXT"
        if not os.path.exists(gcpfile):
            grass.fatal(
                _("Input file with GCPs must be <%s> or <%s>") % ply + ".txt",
                ply + ".TXT",
            )

    if options["output"] is not None and options["output"] != "":
        ply = options["output"]

    clist = list()
    plydesc = grass.read_command("v.in.ply", flags="p", input=infile, output=ply)

    # remember column names for vertices
    currname = ""
    currprop = ""
    for l in plydesc.splitlines():
        f = l.split(":")
        if f[0] == "element name":
            # new element
            currname = f[1].strip()
            currprop = ""
        if f[0] == "property name":
            currprop = f[1].strip()
            if currname == "vertex" and currprop not in ["x", "y", "z"]:
                clist.append(currprop)

    columns = ",".join(clist)

    grass.run_command("v.in.ply", flags="b", input=infile, output=ply)

    # import vector exists?
    found = grass.find_file(ply, element="vector", mapset=currmapset)

    if found["name"] != ply:
        grass.fatal(_("PLY import failed!"))

    # detach table
    table = gvector.vector_layer_db(map=ply, layer=1)["table"]
    grass.run_command("v.db.connect", map=ply, layer=1, flags="d")

    # print RMS
    rmsfile = os.path.join(srcdir, ply + "_rms.csv")
    grass.run_command(
        "v.rectify",
        input=ply,
        output=ply + "_georef",
        points=gcpfile,
        flags="3bor",
        separator=";",
        rmsfile=rmsfile,
    )

    # georectify
    ply_georef = ply + "_georef"
    grass.run_command(
        "v.rectify", input=ply, output=ply_georef, points=gcpfile, flags="3bo"
    )

    # output vector exists?
    found = grass.find_file(ply_georef, element="vector", mapset=currmapset)

    if found["name"] != ply_georef:
        grass.run_command("v.db.connect", map=ply, layer=1, table=table, key="cat")
        grass.fatal("PLY import failed!")

    grass.run_command("v.db.connect", map=ply_georef, layer=1, table=table, key="cat")

    output = os.path.join(srcdir, ply_georef + ".ply")
    grass.run_command("v.out.ply", input=ply_georef, output=output, columns=columns)

    grass.run_command("v.db.connect", map=ply_georef, layer=1, flags="d")

    if export_shifted:
        vinfo = gvector.vector_info(map=ply_georef)
        north_center = (float(vinfo["north"]) + float(vinfo["south"])) / -2.0
        east_center = (float(vinfo["east"]) + float(vinfo["west"])) / -2.0
        height_center = (float(vinfo["top"]) + float(vinfo["bottom"])) / -2.0

        ply_shifted = ply_georef + "_shifted"
        grass.run_command(
            "v.transform",
            input=ply_georef,
            layer=-1,
            output=ply_shifted,
            xshift=east_center,
            yshift=north_center,
            zshift=height_center,
            xscale=1.0,
            yscale=1.0,
            zscale=1.0,
            zrot=0.0,
            flags="b",
        )

        # output vector exists?
        found = grass.find_file(ply_shifted, element="vector", mapset=currmapset)

        if found["name"] != ply_shifted:
            grass.run_command("v.db.connect", map=ply, layer=1, table=table, key="cat")
            grass.fatal("PLY import failed!")

        grass.run_command(
            "v.db.connect", map=ply_shifted, layer=1, table=table, key="cat"
        )

        output = os.path.join(srcdir, ply_shifted + ".ply")
        grass.run_command(
            "v.out.ply", input=ply_shifted, output=output, columns=columns
        )

        grass.run_command("v.db.connect", map=ply_shifted, layer=1, flags="d")

    grass.run_command("v.db.connect", map=ply, layer=1, table=table, key="cat")

    grass.message(
        _(
            "Done: Pointcloud '%s' has been successfully imported, georeferenced, and exported"
        )
        % ply
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
