#!/usr/bin/env python
############################################################################
#
# MODULE:       r.to.vect.tiled
# AUTHOR(S):    Markus Metz
# PURPOSE:      Tiled raster to vector conversion
# COPYRIGHT:    (C) 2014 by the GRASS Development Team
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

# %module
# % description: Converts a raster map into vector tiles.
# % keyword: raster
# % keyword: conversion
# % keyword: geometry
# % keyword: vectorization
# % keyword: tiling
# % overwrite: yes
# %end
# %option G_OPT_R_INPUT
# %end
# %option
# % key: output
# % type: string
# % required: yes
# % multiple: no
# % description: Output base name
# %end
# %option
# % key: type
# % type: string
# % required: yes
# % multiple: no
# % options: point,line,area
# % description: Feature type
# %end
# %option
# % key: column
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % label: Name of attribute column to store value
# % description: Name must be SQL compliant
# % answer: value
# % guisection: Attributes
# %end
# %flag
# % key: s
# % description: Smooth corners of linear features
# %end
# %flag
# % key: v
# % description: Use raster values as categories instead of unique sequence (CELL only)
# % guisection: Attributes
# %end
# %flag
# % key: z
# % label: Write raster values as z coordinate
# % description: Table is not created. Currently supported only for points.
# % guisection: Attributes
# %end
# %flag
# % key: b
# % label: Do not build vector topology
# % description: Recommended for massive point conversion
# %end
# %flag
# % key: t
# % description: Do not create attribute table
# % guisection: Attributes
# %end
# %flag
# % key: p
# % description: Patch the tiles
# %end
# %option
# % key: x
# % type: integer
# % required: no
# % answer: 2
# % multiple: no
# % description: Number of tiles in x direction
# % guisection: Tiling
# %end
# %option
# % key: y
# % type: integer
# % required: no
# % answer: 2
# % multiple: no
# % description: Number of tiles in y direction
# % guisection: Tiling
# %end

import sys

import grass.script as grass


def main():
    input = options["input"]
    output = options["output"]
    column = options["column"]
    ftype = options["type"]
    xtiles = int(options["x"])
    ytiles = int(options["y"])

    rtvflags = ""
    for key in "sbtvz":
        if flags[key]:
            rtvflags += key

    # check options
    if xtiles <= 0:
        grass.fatal(_("Number of tiles in x direction must be > 0"))
    if ytiles < 0:
        grass.fatal(_("Number of tiles in y direction must be > 0"))
    if grass.find_file(name=input)["name"] == "":
        grass.fatal(_("Input raster %s not found") % input)

    grass.use_temp_region()
    curr = grass.region()
    width = int(curr["cols"] / xtiles)
    if width <= 1:
        grass.fatal("The requested number of tiles in x direction is too large")
    height = int(curr["rows"] / ytiles)
    if height <= 1:
        grass.fatal("The requested number of tiles in y direction is too large")

    do_clip = False
    overlap = 0
    if flags["s"] and ftype == "area":
        do_clip = True
        overlap = 2

    ewres = curr["ewres"]
    nsres = curr["nsres"]
    xoverlap = overlap * ewres
    yoverlap = overlap * nsres
    xoverlap2 = (overlap / 2) * ewres
    yoverlap2 = (overlap / 2) * nsres

    e = curr["e"]
    w = curr["w"] + xoverlap
    if w >= e:
        grass.fatal(_("Overlap is too large"))
    n = curr["n"] - yoverlap
    s = curr["s"]
    if s >= n:
        grass.fatal(_("Overlap is too large"))

    datatype = grass.raster_info(input)["datatype"]
    vtiles = None

    # north to south
    for ytile in range(ytiles):
        n = curr["n"] - ytile * height * nsres
        s = n - height * nsres - yoverlap
        if ytile == ytiles - 1:
            s = curr["s"]
        # west to east
        for xtile in range(xtiles):
            w = curr["w"] + xtile * width * ewres
            e = w + width * ewres + xoverlap

            if xtile == xtiles - 1:
                e = curr["e"]

            grass.run_command("g.region", n=n, s=s, e=e, w=w, nsres=nsres, ewres=ewres)

            if do_clip:
                tilename = output + "_stile_" + str(ytile) + str(xtile)
            else:
                tilename = output + "_tile_" + str(ytile) + str(xtile)

            outname = output + "_tile_" + str(ytile) + str(xtile)

            grass.run_command(
                "r.to.vect",
                input=input,
                output=tilename,
                type=ftype,
                column=column,
                flags=rtvflags,
            )

            if do_clip:
                n2 = curr["n"] - ytile * height * nsres - yoverlap2
                s2 = n2 - height * nsres
                if ytile == 0:
                    n2 = curr["n"]
                    s2 = n2 - height * nsres - yoverlap2
                if ytile == ytiles - 1:
                    s2 = curr["s"]

                w2 = curr["w"] + xtile * width * ewres + xoverlap2
                e2 = w2 + width * ewres
                if xtile == 0:
                    w2 = curr["w"]
                    e2 = w2 + width * ewres + xoverlap2
                if xtile == xtiles - 1:
                    e2 = curr["e"]

                tilename = output + "_stile_" + str(ytile) + str(xtile)
                if grass.vector_info_topo(tilename)["areas"] > 0:
                    grass.run_command(
                        "g.region", n=n2, s=s2, e=e2, w=w2, nsres=nsres, ewres=ewres
                    )

                    extname = "extent_tile_" + str(ytile) + str(xtile)
                    grass.run_command("v.in.region", output=extname, flags="d")
                    outname = output + "_tile_" + str(ytile) + str(xtile)
                    grass.run_command(
                        "v.overlay",
                        ainput=tilename,
                        binput=extname,
                        output=outname,
                        operator="and",
                        olayer="0,1,0",
                    )
                    grass.run_command(
                        "g.remove", flags="f", type="vector", name=extname, quiet=True
                    )

                    if vtiles is None:
                        vtiles = outname
                    else:
                        vtiles = vtiles + "," + outname

                grass.run_command(
                    "g.remove", flags="f", type="vector", name=tilename, quiet=True
                )

            else:
                # write cmd history:
                grass.vector_history(outname)
                if vtiles is None:
                    vtiles = outname
                else:
                    vtiles = vtiles + "," + outname

    if flags["p"]:
        grass.run_command("v.patch", input=vtiles, output=output, flags="e")

        grass.run_command("g.remove", flags="f", type="vector", name=vtiles, quiet=True)

        if grass.vector_info_topo(output)["boundaries"] > 0:
            outpatch = output + "_patch"
            grass.run_command("g.rename", vector=(output, outpatch))
            grass.run_command(
                "v.clean", input=outpatch, output=output, tool="break", flags="c"
            )
            grass.run_command("g.remove", flags="f", type="vector", name=outpatch)

    grass.message(_("%s complete") % "r.to.vect.tiled")

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
