#!/usr/bin/env python

############################################################################
#
# MODULE:       d.explanation.plot
# AUTHOR(S):    Vaclav Petras <wenzeslaus gmail com>
#
# PURPOSE:      Draw plot for manual explaining a raster operation
# COPYRIGHT:    (C) 2017-2022 by Vaclav Petras the GRASS Development Team
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
# % required: yes
# % guisection: Rasters
# %end
# %option G_OPT_R_INPUT
# % key: b
# % required: no
# % guisection: Rasters
# %end
# %option G_OPT_R_INPUT
# % key: c
# % required: no
# % guisection: Rasters
# %end
# %option G_OPT_R_INPUT
# % key: d
# % required: no
# % guisection: Rasters
# %end
# %option
# % key: raster_font
# % type: string
# % required: no
# % description: Font for raster numbers
# % guisection: Raster
# %end
# %option
# % key: operator_ab
# % type: string
# % required: no
# % description: Operator between a and b
# % guisection: Operators
# %end
# %option
# % key: operator_bc
# % type: string
# % required: no
# % description: Operator between b and c
# % guisection: Operators
# %end
# %option
# % key: operator_cd
# % type: string
# % required: no
# % description: Operator between c and d
# % guisection: Operators
# %end
# %option
# % key: operator_font
# % type: string
# % required: no
# % description: Font for operators
# % guisection: Operators
# %end
# %option
# % key: label_a
# % type: string
# % required: no
# % description: Label above the raster
# % guisection: Labels
# %end
# %option
# % key: label_b
# % type: string
# % required: no
# % description: Label above the raster
# % guisection: Labels
# %end
# %option
# % key: label_c
# % type: string
# % required: no
# % description: Label above the raster
# % guisection: Labels
# %end
# %option
# % key: label_d
# % type: string
# % required: no
# % description: Label above the raster
# % guisection: Labels
# %end
# %option
# % key: label_font
# % type: string
# % required: no
# % description: Font for labels
# % guisection: Labels
# %end
# %option
# % key: label_size
# % type: double
# % required: no
# % description: Text size for labels
# % guisection: Labels
# %end
# %option
# % key: bottom
# % type: double
# % required: no
# % description: Offset from the bottom (percentage)
# %end

"""Run display commands to render plot explaining raster operations"""

import sys
import os
import grass.script as gs


# Same code as in d.rast.legl ignoring linter suggestions here.
def make_frame(f, b, t, l, r):  # pylint: disable=invalid-name
    """Set frame size from percentages (alternative to d.frame)"""
    # pylint: disable=invalid-name
    (fl, fr, ft, fb) = f

    t /= 100.0
    b /= 100.0
    l /= 100.0
    r /= 100.0

    rt = fb + t * (ft - fb)
    rb = fb + b * (ft - fb)
    rl = fl + l * (fr - fl)
    rr = fl + r * (fr - fl)
    s = "%f,%f,%f,%f" % (rt, rb, rl, rr)  # pylint: disable=consider-using-f-string
    os.environ["GRASS_RENDER_FRAME"] = s


def main():
    """Process command line parameters and do the rendering"""
    # With only 150 lines and many dependencies, this code is likely more clear
    # in one piece.
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements

    options, unused_flags = gs.parser()

    # Parameters are written so that it would not scale well over 4 rasters,
    # but more rasters seems to be too much for this visualization method and style.
    raster_1 = options["a"]
    raster_2 = options["b"]
    raster_3 = options["c"]
    raster_4 = options["d"]

    operator_1 = options["operator_ab"]
    operator_2 = options["operator_bc"]
    operator_3 = options["operator_cd"]

    label_1 = options["label_a"]
    label_2 = options["label_b"]
    label_3 = options["label_c"]
    label_4 = options["label_d"]

    label_font = options["label_font"]
    rast_num_font = options["raster_font"]
    operator_font = options["operator_font"]

    label_font_size = options["label_size"]

    bottom = options["bottom"]
    if bottom:
        bottom = float(bottom)

    # Turn raster individual options into a list, but exclude empty
    # ones at the end of the list.
    rasters = []
    for raster in reversed([raster_1, raster_2, raster_3, raster_4]):
        # Add on first non-empty raster and always after first was added.
        if rasters or raster:
            rasters.insert(0, raster)
    num_rasters = len(rasters)

    # Operators have defaults which depend on number of rasters specified.
    operators = ["+"] * (num_rasters - 2)
    operators.append("->")
    # Values provided by the user overwrite the individual defaults.
    for i, operator in enumerate([operator_1, operator_2, operator_3]):
        if operator and i < len(operators):
            operators[i] = operator

    labels = []
    for raster in [label_1, label_2, label_3, label_4]:
        labels.append(raster)

    # Sizes in the horizontal direction.
    # This is the place to add, e.g., space around for text before and after or add
    # user-specified values.
    # The rest of the content has the same width as one of the rasters.
    width = 100 / (num_rasters + 1)
    if num_rasters == 1:
        # One raster is allowed and this makes the result reasonable.
        space = width / 2
    else:
        # The remaining with is divided between number of spaces
        # and space before and after.
        space = width / num_rasters
    # Start in half of the space to leave half of the space at the end.
    left_start = space / 2

    operator_font_size = space

    # Horizontal positions of objects
    starts = []
    ends = []
    operator_positions = []
    label_positions = []
    for i in range(num_rasters):
        start = left_start + i * width + i * space
        end = start + width
        label = start + width / 2
        operator = end + space / 2
        starts.append(start)
        ends.append(end)
        operator_positions.append(operator)
        label_positions.append(label)

    # Vertical placement follows horizontal to achieve squares and is the
    # same for all objects.
    # Font size is intermixed with the vertical positions to determine spacing
    # based on font size, but also provide default if needed.
    height = width
    if not label_font_size:
        label_font_size = height / 6
    if not bottom:
        bottom = label_font_size
    top = bottom + height
    operator_height = bottom + height / 2
    label_height = top + label_font_size

    # Although we set things explicitly for customization,
    # set font also globally (for the process) for things we don't set.
    if label_font:
        os.environ["GRASS_FONT"] = label_font

    # We generate one extra operator position, so we limit iteration only to operators.
    for operator, position in zip(operators, operator_positions[: len(operators)]):
        gs.run_command(
            "d.text",
            text=operator,
            color="black",
            at=(position, operator_height),
            align="cc",
            font=operator_font,
            size=operator_font_size,
        )

    # Use can provide extra labels, but we will draw only the ones for rasters.
    for label, position in zip(labels[: len(rasters)], label_positions[: len(rasters)]):
        if label:
            gs.run_command(
                "d.text",
                text=label,
                color="black",
                at=(position, label_height),
                align="cc",
                font=label_font,
                size=label_font_size,
            )

    # Current frame (or whole screen)
    frame_info = gs.read_command("d.info", flags="f", errors="fatal")
    frame_info = frame_info.split(":")[1]
    top_frame = tuple(float(x) for x in frame_info.split())

    # Rendering
    for raster, start, end in zip(rasters, starts, ends):
        # Skips not filled rasters.
        if raster:
            make_frame(top_frame, bottom, top, start, end)
            gs.run_command("d.rast", map=raster)
            gs.run_command(
                "d.rast.num", map=raster, font=rast_num_font, grid_color="#444444"
            )


if __name__ == "__main__":
    sys.exit(main())
