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
# SPDX-FileCopyrightText: 2016 Alexander Muriy /
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
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
    import grass.script as gs
except:
    try:
        from grass.script import core as gs
    except:
        if "GISBASE" not in os.environ:
            print("You must be in GRASS GIS to run this program.")
            sys.exit(1)


def cleanup():
    with open(os.devnull, "w") as nuldev:
        gs.run_command(
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
    if not gs.find_file(inmap, element="vector")["file"]:
        gs.fatal(_("<%s> does not exist.") % inmap)

    out_split = "v_explode" + "_" + "split"
    gs.run_command(
        "v.split", input_=inmap, vertices=2, out=out_split, quiet=True, stderr=None
    )
    out_catdel = "v_explode" + "_" + "catdel"
    gs.run_command(
        "v.category",
        input_=out_split,
        opt="del",
        output=out_catdel,
        quiet=True,
        stderr=None,
    )
    gs.run_command(
        "v.category",
        input_=out_catdel,
        opt="add",
        output=outmap,
        quiet=True,
        stderr=None,
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
