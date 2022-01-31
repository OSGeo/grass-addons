#!/usr/bin/env python
############################################################################
#
# MODULE:       d.vect.colboxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws the boxplot(s) of values in a vector attribute column
#
# COPYRIGHT:    (c) 2019 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws the boxplot of values in a vector attribute column
# % keyword: display
# % keyword: vector
# % keyword: plot
# % keyword: histogram
# % keyword: boxplot
# %end

# %option G_OPT_V_MAP
# % guisection: General
# %end

# %option G_OPT_V_FIELD
# %end

# %option G_OPT_DB_COLUMN
# % key: column
# % description: Attribute column value to be plotted
# % required: yes
# % guisection: General
# %end

# %option G_OPT_DB_WHERE
# %guisection: General
# %end

# %option G_OPT_F_OUTPUT
# % key: plot_output
# % required: no
# % guisection: General
# %end

# %option G_OPT_DB_COLUMN
# % key: group_by
# % description: Attribute column with categories to group the data by
# % required: no
# % guisection: Plot options
# %end

# %option
# % key: order
# % type: string
# % label: Sort boxplots
# % description: Sort boxplots based on their median values
# % required: no
# % options: descending,ascending
# % guisection: Plot options
# %end

# %flag
# % key: h
# % label: horizontal boxplot(s)
# % description: Draw the boxplot horizontal
# % guisection: Plot options
# %end

# %flag
# % key: o
# % label: hide outliers
# % description: Draw boxplot(s) without outliers
# % guisection: Plot options
# %end

# %flag
# % key: n
# % label: notch
# % description: Draw boxplot(s) with notch
# % guisection: Plot options
# %end

# %flag
# % key: r
# % label: Rotate labels
# % description: rotate x-axis labels
# % guisection: Plot options
# %end

import sys
import grass.script as gscript
import operator
import numpy as np


def main():
    import matplotlib  # required by windows

    matplotlib.use("wxAGG")  # required by windows
    import matplotlib.pyplot as plt

    # input
    vector = options["map"]
    column = options["column"]
    group_by = options["group_by"] if options["group_by"] else None
    output = options["plot_output"] if options["plot_output"] else None
    where = (
        options["where"] + " AND " + column + " IS NOT NULL"
        if options["where"]
        else column + " IS NOT NULL"
    )
    sort = options["order"] if options["order"] else None
    if sort == "descending":
        reverse = True
    elif sort == "ascending":
        reverse = False
    else:
        reverse = None
    cols = filter(None, [group_by, column])
    flag_h = not flags["h"]
    flag_o = not flags["o"]
    flag_n = flags["n"]
    flag_r = flags["r"]

    # Get data with where clause
    if where:
        df = [
            x
            for x in gscript.read_command(
                "v.db.select", map_=vector, column=cols, where=where, flags="c"
            ).splitlines()
        ]
    # Get all column data
    else:
        df = [
            x
            for x in gscript.read_command(
                "v.db.select", map_=vector, column=cols, flags="c"
            ).splitlines()
        ]
    # for grouped boxplot
    if group_by:
        # Split columns and create list with data and with labels
        df = [x.split("|") for x in df]
        vals = [float(i[1]) for i in df]
        groups = [i[0] for i in df]
        uid = list(set(groups))
        data = []
        sf = []
        for i, m in enumerate(uid):
            a = [j for j, grp in enumerate(groups) if grp == m]
            data.append([vals[i] for i in a])
            sf.append([m, np.median([vals[i] for i in a])])

        # Order boxes
        if sort:
            sf.sort(key=operator.itemgetter(1), reverse=reverse)
        sf = [i[0] for i in sf]
        ii = {e: i for i, e in enumerate(sf)}
        sfo = [(ii[e]) for i, e in enumerate(uid) if e in ii]

        # Draw boxplot
        plt.boxplot(
            data,
            notch=flag_n,
            sym="gD",
            labels=uid,
            vert=flag_h,
            showfliers=flag_o,
            positions=sfo,
        )
    else:
        data = [float(x) for x in df]
        plt.boxplot(data, notch=flag_n, sym="gD", vert=flag_h, showfliers=flag_o)
    if flag_r:
        plt.xticks(rotation=90)
    plt.tight_layout()
    if output:
        plt.savefig(output)
    else:
        plt.show()


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
