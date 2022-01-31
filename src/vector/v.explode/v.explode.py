#!/usr/bin/env python

############################################################################
#
# MODULE:       v.explode
# AUTHOR(S):    Alexander Muriy
#               (Institute of Environmental Geoscience, Moscow, Russia)
#               e-mail: amuriy AT gmail DOT com
#
# PURPOSE:      "Explode" polylines, splitting them to separate lines
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
# %  description: "Explode" polylines, splitting them to separate lines (uses v.split + v.category)
# %  keyword: display
# %  keyword: graphics
# %  keyword: vector
# %  keyword: symbology
# %End
# %Option
# %  key: input
# %  type: string
# %  required: yes
# %  multiple: no
# %  key_desc: name
# %  description: Name of input vector map
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
############################################################################

import os
import atexit

try:
    import grass.script as grass
except:
    try:
        from grass.script import core as grass
    except:
        if "GISBASE" not in os.environ:
            print("You must be in GRASS GIS to run this program.")
            sys.exit(1)


def cleanup():
    with open(os.devnull, "w") as nuldev:
        grass.run_command(
            "g.remove",
            type_="vect",
            pattern="v_explode*",
            flags="f",
            quiet=True,
            stderr=nuldev,
        )


def main():
    inmap = options["input"]
    outmap = options["output"]

    # check if input file exists
    if not grass.find_file(inmap, element="vector")["file"]:
        grass.fatal(_("<%s> does not exist.") % inmap)

    out_split = "v_explode" + "_" + "split"
    grass.run_command(
        "v.split", input_=inmap, vertices=2, out=out_split, quiet=True, stderr=None
    )
    out_catdel = "v_explode" + "_" + "catdel"
    grass.run_command(
        "v.category",
        input_=out_split,
        opt="del",
        output=out_catdel,
        quiet=True,
        stderr=None,
    )
    grass.run_command(
        "v.category",
        input_=out_catdel,
        opt="add",
        output=outmap,
        quiet=True,
        stderr=None,
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
