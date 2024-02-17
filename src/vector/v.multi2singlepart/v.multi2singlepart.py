#!/usr/bin/env python

#
############################################################################
#
# MODULE:       v.multi2singlepart
# AUTHOR(S):    Paulo van Breugel
# PURPOSE:      Split multipart polygons into singlepart polygon features
#
# COPYRIGHT:   (C) 2024 Paulo van Breugel and the GRASS Development Team
#              http://ecodiv.earth
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
# REQUIREMENTS:
# -
# %module
# % description: Split multi-polygon features into single polygon features.
# % keyword: vector
# % keyword: geometry
# %end

# %option G_OPT_V_INPUT
# % description: Input vector layer
# % required: yes
# %end

# %option G_OPT_V_OUTPUT
# % description: Output vector layer
# % required: yes
# %end

# ----------------------------------------------------------------------------
# Standard
# ----------------------------------------------------------------------------

# import libraries
import sys
import atexit
import sys
import uuid
import grass.script as gs


CLEAN_LAY = []


def create_temporary_name(prefix):
    tmpf = f"{prefix}{str(uuid.uuid4().hex)}"
    CLEAN_LAY.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps specified in the global list"""
    maps = reversed(CLEAN_LAY)
    mapset = gs.gisenv()["MAPSET"]
    for map_name in maps:
        for element in ("raster", "vector"):
            found = gs.find_file(
                name=map_name,
                element=element,
                mapset=mapset,
            )
            if found["file"]:
                gs.run_command(
                    "g.remove",
                    flags="f",
                    type=element,
                    name=map_name,
                    quiet=True,
                )


def main(options, flags):

    # Copy layer and remove all but cat column in new layer
    tmplayer = create_temporary_name("tmp")
    gs.run_command("g.copy", vector=[options["input"], tmplayer], overwrite=True)
    cols = gs.read_command("db.columns", table=tmplayer).split("\n")
    cols = [x for x in cols[1:] if x != ""]
    gs.run_command("v.db.dropcolumn", map=tmplayer, columns=cols)

    # Overlay the original and copied layer
    gs.run_command(
        "v.overlay",
        ainput=options["input"],
        binput=tmplayer,
        operator="and",
        output=options["output"],
    )

    # Drop old cat columns
    gs.run_command("v.db.dropcolumn", map=options["output"], columns=["a_cat", "b_cat"])

    # Change the column names to the original names
    for colname in cols:
        oldcol = f"a_{colname}"
        gs.run_command(
            "v.db.renamecolumn", map=options["output"], column=[oldcol, colname]
        )


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
