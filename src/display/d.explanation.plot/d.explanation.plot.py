#!/usr/bin/env python

############################################################################
#
# MODULE:       d.explanation.plot
# AUTHOR(S):    Vaclav Petras <wenzeslaus gmail com>
#
# PURPOSE:      Draw plot for manual explaining a raster operation
# COPYRIGHT:    (C) 2017 by Vaclav Petras the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Draw a plot of multiple rasters to explain a raster operation for example a + b = c
# % keyword: display
# % keyword: manual
# % keyword: raster
# %end
# %option G_OPT_R_INPUT
# % key: a
# %end
# %option G_OPT_R_INPUT
# % key: b
# %end
# %option G_OPT_R_INPUT
# % key: c
# %end
# %option
# % key: label_a
# % type: string
# % required: no
# % description: Label above the raster
# %end
# %option
# % key: label_b
# % type: string
# % required: no
# % description: Label above the raster
# %end
# %option
# % key: label_c
# % type: string
# % required: no
# % description: Label above the raster
# %end


import sys
import os
import grass.script as gs

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))


def main():
    options, flags = gs.parser()

    raster_1 = options["a"]
    raster_2 = options["b"]
    raster_3 = options["c"]

    # TODO: add also labels below the images
    label_1 = options["label_a"]
    label_2 = options["label_b"]
    label_3 = options["label_c"]

    # TODO: make fonts customizable
    label_font = "FreeSans:Regular"
    rast_num_font = "FreeMono:Regular"
    operator_font = "FreeMono:Regular"

    # TODO: make sizes customizable
    label_font_size = 6
    operator_font_size = 10

    # although we set things explicitly for customization,
    # set font also globally (for the process) for things we don't set
    os.environ["GRASS_FONT"] = label_font

    # TODO: move the positions to variables, esp. the centered things
    # and the initial vertical position

    # TODO: add operators/text before and after the raster images
    # TODO: make the operators customizable
    gs.run_command(
        "d.text",
        text="+",
        color="black",
        at=(33, 40),
        align="cc",
        font=operator_font,
        size=operator_font_size,
    )
    gs.run_command(
        "d.text",
        text="->",
        color="black",
        at=(66, 40),
        align="cc",
        font=operator_font,
        size=operator_font_size,
    )

    if label_1:
        gs.run_command(
            "d.text",
            text=label_1,
            color="black",
            at=(10, 60),
            align="cc",
            font=label_font,
            size=label_font_size,
        )
    if label_2:
        gs.run_command(
            "d.text",
            text=label_2,
            color="black",
            at=(45, 60),
            align="cc",
            font=label_font,
            size=label_font_size,
        )
    if label_3:
        gs.run_command(
            "d.text",
            text=label_3,
            color="black",
            at=(80, 60),
            align="cc",
            font=label_font,
            size=label_font_size,
        )

    # TODO: create frames internally using the env variable so that the
    # subsequent commands are not influenced

    gs.run_command("d.frame", frame="f1", at=(25, 50, 5, 30), flags="c")
    gs.run_command("d.rast", map=raster_1)
    gs.run_command("d.rast.num", map=raster_1, font=rast_num_font)
    gs.run_command("d.frame", frame="f2", at=(25, 50, 40, 65), flags="c")
    gs.run_command("d.rast", map=raster_2)
    gs.run_command("d.rast.num", map=raster_2, font=rast_num_font)
    # TODO: third one should be optional for: a -> b
    gs.run_command("d.frame", frame="f3", at=(25, 50, 75, 100), flags="c")
    gs.run_command("d.rast", map=raster_3)
    gs.run_command("d.rast.num", map=raster_3, font=rast_num_font)
    # TODO: add fourth one for: a + b + c -> d
    # (more seems to be too much for this method and style)


if __name__ == "__main__":
    sys.exit(main())
