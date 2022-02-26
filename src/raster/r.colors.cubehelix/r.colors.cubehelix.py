#!/usr/bin/env python

#
############################################################################
#
# MODULE:       r.colors.cubehelix
# AUTHOR:       Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:      Convert a GMT color table into a GRASS color rules file
# COPYRIGHT:    (C) 2007 by Vaclav Petras, Anna Petrasova
#               and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Create or apply a cubehelix color table to a GRASS raster map
# % keyword: raster
# % keyword: color table
# % keyword: cubehelix
# % keyword: seaborn
# %end

# %option G_OPT_R_MAPS
# % description: Raster map(s) to apply color table to
# % required: no
# % guisection: Basic
# %end
# %option G_OPT_F_OUTPUT
# % description: Name for the new color table rules file
# % required: no
# %end

# %option
# % key: start
# % type: double
# % description: The hue at the start of the helix
# % options: 0-3
# % answer: 0
# % required: no
# % guisection: Cubehelix
# %end
# %option
# % key: nrotations
# % type: double
# % label: Rotations around the hue wheel
# % description: Rotations around the hue wheel over the range of the color table
# % options: 0-3
# % answer: 0.4
# % required: no
# % guisection: Cubehelix
# %end
# %option
# % key: gamma
# % type: double
# % description: Gamma factor to emphasize darker (<1) or lighter (>1) colors
# % options: 0-
# % answer: 1.0
# % required: no
# % guisection: Cubehelix
# %end
# %option
# % key: hue
# % type: double
# % description: Saturation of the colors
# % options: 0-1
# % answer: 0.8
# % required: no
# % guisection: Cubehelix
# %end
# %option
# % key: light
# % type: double
# % description: Intensity of the lightest color in the color table
# % options: 0-1
# % answer: 0.85
# % required: no
# % guisection: Cubehelix
# %end
# %option
# % key: dark
# % type: double
# % description: Intensity of the darkest color in the color table
# % options: 0-1
# % answer: 0.15
# % required: no
# % guisection: Cubehelix
# %end

# %option
# % key: ncolors
# % type: integer
# % label: Number of colors in the color table
# % description: Number of color intervals in a discrete color table with -d
# % options: 2-
# % answer: 6
# % required: no
# % guisection: Rules
# %end
# %flag
# % key: d
# % label: Generate discrete color table
# % description: Generate discrete (interval) color table instead of a continuous one
# % guisection: Rules
# %end

# %flag
# % key: n
# % label: Reverse the order of colors (invert colors)
# % description: If set, the color table will go from dark to light
# % guisection: Basic
# %end
# %flag
# % key: g
# % description: Logarithmic scaling
# % guisection: Basic
# %end
# %flag
# % key: a
# % description: Logarithmic-absolute scaling
# % guisection: Basic
# %end
# %flag
# % key: e
# % description: Histogram equalization
# % guisection: Basic
# %end
# %rules
# % requires: -g, map
# % requires: -a, map
# % requires: -e, map
# %end


import os
import sys
import grass.script as gscript


def values_to_rule(value, red, green, blue, percent):
    """Return textual representation of one color rule line"""
    return "{v:.3f}{p} {r}:{g}:{b}".format(
        v=value, p="%" if percent else "", r=red, g=green, b=blue
    )


# sync with r.colors.matplotlib
# this can potentially go to the core as something like grass.utils
def mpl_cmap_to_rules(cmap, n_colors=None, discrete=False, comments=None):
    if not n_colors:
        n_colors = cmap.N
    # determine numbers for recomputing from absolute range to relative
    cmin = 0
    cmax = n_colors
    if not discrete:
        cmax -= 1
    crange = cmax - cmin
    cinterval = float(crange) / n_colors

    rules = []
    if comments:
        for comment in comments:
            rules.append("# {}".format(comment))
    for v1 in range(0, n_colors, 1):
        r1, g1, b1 = cmap(v1)[:3]
        if discrete:
            v2 = v1 + cinterval
        v1 = 100 * (crange - (cmax - v1)) / float(crange)
        if discrete:
            v2 = 100 * (crange - (cmax - v2)) / float(crange)
        # multiply to get 255 after integer
        # assuming nobody uses smaller faction than 0.001
        # taken from color_rules.c
        r1 = int(r1 * 255.999)
        g1 = int(g1 * 255.999)
        b1 = int(b1 * 255.999)
        rules.append(values_to_rule(value=v1, red=r1, green=g1, blue=b1, percent=True))
        if discrete:
            rules.append(
                values_to_rule(value=v2, red=r1, green=g1, blue=b1, percent=True)
            )
    return "\n".join(rules)


def main(options, flags):
    # TODO: inervals flag, s should be defaut behavior
    n_colors = int(options["ncolors"])
    discrete = flags["d"]

    fallback = True
    try:
        import seaborn as sns

        fallback = False
    except ImportError:
        # perhaps this can be function in the core
        gscript.error(_("{} Python package not installed.").format("seaborn"))
    if not fallback:
        cmap = sns.cubehelix_palette(
            n_colors=n_colors,
            start=float(options["start"]),
            rot=float(options["nrotations"]),
            gamma=float(options["gamma"]),
            hue=float(options["hue"]),
            light=float(options["light"]),
            dark=float(options["dark"]),
            reverse=flags["n"],
            as_cmap=False,
        )
        # as_cmap ignores n_colors in 0.7.0
        # but we want n_colors to be exact when we are exporting
        # the color table or doing discrete one
        import matplotlib  # required by windows

        matplotlib.use("wxAGG")  # required by windows
        import matplotlib.colors as clr

        cmap = clr.LinearSegmentedColormap.from_list("from_list", cmap, N=n_colors)
    else:
        gscript.warning(
            _(
                "Using Matplotlib cubehelix color table."
                " Most of cubehelix parameters ignored"
            )
        )
        # we are very nice and provide a fallback
        import matplotlib.pyplot as plt

        name = "cubehelix"
        # Matplotlib one goes from dark to light but Seaborn goes
        # the other way around by default
        if not flags["n"]:
            name += "_r"
        cmap = plt.get_cmap(name, lut=n_colors)

    comments = []
    comments.append("Cubehelix color table generated using:")
    command = [sys.argv[0].split(os.path.sep)[-1]]
    command.extend(sys.argv[1:])
    comments.append("  {}".format(" ".join(command)))

    rules = mpl_cmap_to_rules(
        cmap, n_colors=n_colors, discrete=discrete, comments=comments
    )

    if options["map"]:
        rcf = ""
        for char in "gae":
            if flags[char]:
                rcf += char
        gscript.write_command(
            "r.colors",
            map=options["map"],
            flags=rcf,
            rules="-",
            stdin=rules,
        )
    if options["output"]:
        with open(options["output"], "w") as f:
            f.write(rules)
            f.write("\n")
    elif not options["map"]:
        print(rules)


if __name__ == "__main__":
    sys.exit(main(*gscript.parser()))
