#!/usr/bin/env python
############################################################################
#
# MODULE:       v.boxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws the boxplot(s) of values in a vector attribute column
#
# COPYRIGHT:    (c) 2019-2024 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws a boxplot of values from a specified attribute column in a vector dataset, with an optional grouping based on categories in another column.
# % keyword: display
# % keyword: vector
# % keyword: plot
# % keyword: histogram
# % keyword: boxplot
# %end

# %option G_OPT_V_MAP
# % guisection: Input
# %end

# %option G_OPT_V_FIELD
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: column
# % description: Attribute column value to be plotted
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: group_by
# % description: Attribute column with categories to group the data by
# % required: no
# % guisection: Input
# %end

# %option G_OPT_DB_WHERE
# %guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# % label: Name of output image file
# % guisection: Output
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions (width,height)
# % description: Dimensions (width,height) of the figure in inches
# % required: no
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: resolution of plot
# % required: no
# % answer: 100
# % guisection: Output
# %end

# %option
# % key: fontsize
# % type: integer
# % label: Font size
# % answer: 10
# % description: Default font size
# % guisection: Output
# % required: no
# %end

# %option
# % key: order
# % type: string
# % label: Sort boxplots
# % description: Sort boxplots based on their median values
# % required: no
# % options: descending,ascending
# % guisection: Plot format
# %end

# %flag
# % key: h
# % label: horizontal boxplot(s)
# % description: Draw the boxplot horizontal
# % guisection: Plot format
# %end

# %flag
# % key: o
# % label: Include outliers
# % description: Draw boxplot(s) with outliers
# % guisection: Plot format
# %end

# %flag
# % key: n
# % label: notch
# % description: Draw boxplot(s) with notch
# % guisection: Plot format
# %end

# %flag
# % key: r
# % label: Rotate labels
# % description: rotate x-axis labels
# % guisection: Plot format
# %end

# %flag
# % key: g
# % label: Add grid lines
# % description: Add grid lines
# % guisection: Plot format
# %end

# %option
# % key: axis_limits
# % type: string
# % label: Limit value axis [min,max]
# % description: min and max value of y-axis, or x-axis if -h flag is set)
# % guisection: Plot format
# % required: no
# %end

# %option G_OPT_CN
# % key: bx_color
# % label: Color of the boxplots
# % description: Color of boxplots
# % required: no
# % answer: white
# % guisection: Boxplot format
# %end

# %option G_OPT_CN
# % key: bx_blcolor
# % label: Color of the borders of the boxplots
# % description: Color of the borderlines of the boxplots
# % required: no
# % answer: black
# % guisection: Boxplot format
# %end

# %option
# % key: bx_width
# % type: double
# % label: Boxplot width
# % description: The width of the boxplots (0,1])
# % required: no
# % guisection: Boxplot format
# % answer: 0.75
# % options: 0.1-1
# %end

# %option
# % key: bx_lw
# % type: double
# % label: boxplot linewidth
# % description: The boxplots border, whisker and cap line width
# % required: no
# % guisection: Boxplot format
# % answer: 1
# %end

# %option
# % key: median_lw
# % type: double
# % description: width of the boxplot median line
# % required: no
# % guisection: Boxplot format
# % answer: 1.1
# %end

# %option G_OPT_C
# % key: median_color
# % label: Color of the boxlot median line
# % description: Color of median
# % required: no
# % answer: orange
# % guisection: Boxplot format
# %end

# %option
# % key: flier_marker
# % type: string
# % label: Flier marker
# % description: Set flier marker (see https://matplotlib.org/stable/api/markers_api.html for options)
# % required: no
# % answer: o
# % guisection: Boxplot format
# %end

# %option
# % key: flier_size
# % type: string
# % label: Flier size
# % description: Set the flier size
# % required: no
# % answer: 2
# % guisection: Boxplot format
# %end

# %option G_OPT_C
# % key: flier_color
# % label: Flier color
# % description: Set the flier color
# % required: no
# % answer: black
# % guisection: Boxplot format
# %end

import sys
import grass.script as gs
import operator
import numpy as np


def lazy_import_py_modules(backend):
    """Lazy import Py modules"""
    global matplotlib
    global plt

    # lazy import matplotlib
    try:
        import matplotlib

        if backend is None:
            matplotlib.use("WXAgg")
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is not installed. Please, install it."))


def get_valid_color(color):
    """Get valid Matplotlib color

    :param str color: input color

    :return str|list: color e.g. blue|[0.0, 0.0, 1.0]
    """
    if ":" in color:
        color = [int(x) / 255 for x in color.split(":")]
    if not matplotlib.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.".format(color)))
    return color


def main():

    # lazy import matplotlib
    output = options["output"] if options["output"] else None
    lazy_import_py_modules(output)

    # input
    vector = options["map"]
    column = options["column"]
    dpi = float(options["dpi"])
    grid = flags["g"]
    if options["plot_dimensions"]:
        dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    else:
        if flags["h"]:
            dimensions = [6, 4]
        else:
            dimensions = [4, 6]
    blcolor = get_valid_color(options["bx_blcolor"])
    bxcolor = get_valid_color(options["bx_color"])
    boxprops = {
        "color": blcolor,
        "facecolor": bxcolor,
        "linewidth": float(options["bx_lw"]),
    }
    median_color = get_valid_color(options["median_color"])
    medianprops = {
        "color": median_color,
        "linewidth": float(options["median_lw"]),
    }
    whiskerprops = {
        "linewidth": float(options["bx_lw"]),
        "color": blcolor,
    }
    capprops = {
        "linewidth": float(options["bx_lw"]),
        "color": blcolor,
    }
    flier_color = get_valid_color(options["flier_color"])
    flierprops = {
        "marker": options["flier_marker"],
        "markersize": float(options["flier_size"]),
        "markerfacecolor": flier_color,
        "markeredgecolor": flier_color,
        "markeredgewidth": float(options["bx_lw"]),
    }
    bxp_width = float(options["bx_width"])
    group_by = options["group_by"] if options["group_by"] else None
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
    flag_o = flags["o"]
    flag_n = flags["n"]
    flag_r = flags["r"]

    # Get data with where clause
    if where:
        df = [
            x
            for x in gs.read_command(
                "v.db.select", map_=vector, column=cols, where=where, flags="c"
            ).splitlines()
        ]
    # Get all column data
    else:
        df = [
            x
            for x in gs.read_command(
                "v.db.select", map_=vector, column=cols, flags="c"
            ).splitlines()
        ]

    # Set plot dimensions and fontsize
    if bool(options["fontsize"]):
        plt.rcParams["font.size"] = int(options["fontsize"])

    # Closing message
    if not options["output"]:
        gs.message(
            _("\n> Note, you need to close the figure to finish the script \n\n")
        )

    # Set plot dimensions and DPI
    fig, ax = plt.subplots(figsize=dimensions, dpi=dpi)

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
        ax.boxplot(
            data,
            notch=flag_n,
            labels=uid,
            vert=flag_h,
            showfliers=flag_o,
            positions=sfo,
            boxprops=boxprops,
            medianprops=medianprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            flierprops=flierprops,
            patch_artist=True,
            widths=bxp_width,
        )
    else:
        data = [float(x) for x in df]
        ax.boxplot(
            data,
            notch=flag_n,
            vert=flag_h,
            showfliers=flag_o,
            boxprops=boxprops,
            medianprops=medianprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            flierprops=flierprops,
            patch_artist=True,
            widths=bxp_width,
        )
    if flag_r:
        plt.xticks(rotation=90)
    plt.tight_layout()

    # Set limits value axis
    if bool(options["axis_limits"]):
        minlim, maxlim = map(float, options["axis_limits"].split(","))
        if bool(flag_h):
            plt.ylim([minlim, maxlim])
        else:
            plt.xlim([minlim, maxlim])

    # Set grid (optional)
    if flag_h:
        ax.yaxis.grid(bool(grid))
    else:
        ax.xaxis.grid(bool(grid))

    if output:
        plt.savefig(output)
    else:
        plt.show()


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
