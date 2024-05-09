#!/usr/bin/env python
############################################################################
#
# MODULE:       v.histogram
# AUTHOR:       Moritz Lennert
# PURPOSE:      Draws the histogram of values in a vector attribute column
#
# COPYRIGHT:    (c) 2017 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws the histogram of values in a vector attribute column
# % keyword: vector
# % keyword: plot
# % keyword: histogram
# %end
# %option G_OPT_V_MAP
# %end
# %option G_OPT_V_FIELD
# %end
# %option G_OPT_DB_COLUMN
# % key: column
# % description: Attribute column to create histogram from
# % required: yes
# %end
# %option G_OPT_DB_WHERE
# %end
# %option G_OPT_F_OUTPUT
# % label: Name for graphic output file for plot (extension decides format, - for screen)
# % required: yes
# % answer: -
# %end
# %option
# % key: bins
# % type: integer
# % description: Number of bins in histogram
# % answer: 30
# % required: no
# %end


import sys
import grass.script as gscript


def main():
    import matplotlib  # required by windows

    matplotlib.use("wxAGG")  # required by windows
    import matplotlib.pyplot as plt

    vector = options["map"]
    layer = options["layer"]
    column = options["column"]
    bins = int(options["bins"])
    plot_output = options["output"]
    where = options["where"] if options["where"] else None

    if where:
        data = [
            float(x)
            for x in gscript.read_command(
                "v.db.select",
                map_=vector,
                layer=layer,
                column=column,
                where=where,
                flags="c",
            ).splitlines()
        ]
    else:
        data = [
            float(x)
            for x in gscript.read_command(
                "v.db.select", map_=vector, layer=layer, column=column, flags="c"
            ).splitlines()
        ]

    plt.hist(data, bins=bins)
    if plot_output == "-":
        plt.show()
    else:
        plt.savefig(plot_output)


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
