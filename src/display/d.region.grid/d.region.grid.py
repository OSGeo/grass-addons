#!/usr/bin/env python3

############################################################################
#
# MODULE:        d.shade
# AUTHOR(S):     Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:
# COPYRIGHT:     (C) 2021 by Vaclav Petras and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Drapes a color raster over an shaded relief or aspect map.
# % keyword: display
# % keyword: elevation
# % keyword: relief
# % keyword: hillshade
# % keyword: visualization
# %end
# %option G_OPT_M_REGION
# % required: no
# % label: Use an existing saved region
# % description:
# %end
# %option G_OPT_R_MAP
# % key: raster
# % required: no
# % label: Use a raster map
# % description:
# %end
# %option G_OPT_C
# % description: Grid color
# % answer: gray
# %end
# %option
# % key: width
# % type: double
# % required: no
# % multiple: no
# % description: Grid line width
# %end
# %flag
# % key: r
# % label: Use the current computation region
# % description: This will not work in cases when region is handled in a special way such as GUI
# %end
# %rules
# % required: region, raster, -r
# % exclusive: region, raster, -r
# %end

"""Draw grid of a computational region using d.grid"""

import os

import grass.script as gs


def main():
    """Process command line parameters and do the rendering"""
    options, flags = gs.parser()

    region = options["region"]
    raster = options["raster"]
    color = options["color"]
    width = options["width"]

    grid_flags = "bt"
    if region:
        region = gs.parse_command("g.region", region=region, flags="gu")
        origin = (region["e"], region["n"])
    elif raster:
        region = gs.parse_command("g.region", raster=raster, flags="gu")
        origin = (region["e"], region["n"])
    elif flags["r"]:
        region = gs.parse_command("g.region", flags="gu")
        grid_flags += "a"
        origin = None
    else:
        raise RuntimeError(_("Unhandled option combination"))
    nsres = region["nsres"]
    ewres = region["ewres"]

    # In many cases, the resolutions will be the same and will pass a simple
    # equality test as strings. If that's the case, we really need to call
    # just one d.grid.
    if nsres == ewres:
        first_direction = "both"
        render_second = False
    else:
        first_direction = "east-west"
        render_second = True

    gs.run_command(
        "d.grid",
        size=nsres,
        origin=origin,
        direction=first_direction,
        color=color,
        width=width,
        flags=grid_flags,
        errors="fatal",
    )

    if not render_second:
        # No further rendering needed. We are done.
        return

    os.environ["GRASS_RENDER_FILE_READ"] = "TRUE"
    gs.run_command(
        "d.grid",
        size=ewres,
        origin=origin,
        direction="north-south",
        color=color,
        width=width,
        flags=grid_flags,
        errors="fatal",
    )


if __name__ == "__main__":
    main()
