#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.scatterplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Plots the values of two columns in the attribute table
#               of an input vector layer in a scatterplot.
#
# COPYRIGHT:    (c) 2023 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Plots the values of two columns in the attribute table of an input vector layer in a scatterplot.
# % keyword: display
# % keyword: vector
# % keyword: plot
# % keyword: scatterplot
# %end

# %option G_OPT_V_MAP
# % key: map
# % description: input vector layer
# % required: yes
# % label: Input map
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: x
# % description: Column with X values
# % required: yes
# % label: X column
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: y
# % description: Column with Y values
# % required: yes
# % label: Y column
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key: file_name
# % label: Name of the output file (extension decides format)
# % required: no
# % guisection: Output
# %end

# %option
# % key: title
# % type: string
# % label: Plot title
# % description: The title of the plot
# % required: no
# % guisection: Aesthetics
# %end

# %option
# % key: marker
# % type: string
# % label: Dot marker
# % description: Set dot marker (see https://matplotlib.org/stable/api/markers_api.html for options)
# % required: no
# % answer: o
# % guisection: Aesthetics
# %end

# %option G_OPT_C
# % key: color
# % type: string
# % label: Dot color
# % description: Color of dots
# % required: no
# % answer: blue
# % guisection: Aesthetics
# %end

# %option G_OPT_C
# % key: line_color
# % type: string
# % label: Color trendline
# % description: Color of the trendline
# % required: no
# % answer: darkgrey
# % guisection: Aesthetics
# %end

# %option
# % key: line_style
# % type: string
# % label: Line style trendline
# % description: Line style trendline
# % required: no
# % answer: --
# % guisection: Aesthetics
# %end

# %option
# % key: line_width
# % type: double
# % label: trendline width
# % description: Line width of the trendline
# % required: no
# % answer: 2
# % guisection: Aesthetics
# %end

# %option
# % key: fontsize
# % type: double
# % label: Font size
# % answer: 10
# % description: Default font size
# % guisection: Aesthetics
# % required: no
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions (width,height)
# % description: Dimensions (width,height) of the figure in inches
# % required: no
# % answer: 6,4
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: resolution of plot
# % required: no
# % answer: 96
# % guisection: Output
# %end

# %option
# % key: type
# % type: string
# % label: plot type
# % description: Type of plot (scatter, density)
# % required: no
# % answer: scatter
# % options: scatter, density
# % guisection: Stats
# %end

# %option
# % key: bins
# % type: string
# % label: 2D bins
# % description: The number of bins in x and y dimension.
# % required: no
# % answer: 30,30
# % guisection: Stats
# %end

# %option
# % key: trendline
# % type: string
# % label: Trendline
# % description: Plot trendline
# % required: no
# % options: linear, polynomial
# % guisection: Stats
# %end

# %option
# % key: degree
# % type: integer
# % label: Degree
# % description: Degree polynomial trendline
# % required: no
# % answer: 1
# % guisection: Stats
# %end

import atexit
import sys
import uuid
import numpy as np
from subprocess import PIPE
import grass.script as gs
from grass.pygrass.modules import Module
from numpy.polynomial import Polynomial


def lazy_import_matplotlib():
    """Lazy import matplotlib modules"""
    global matplotlib
    global plt
    global cm
    global Normalize
    try:
        import matplotlib

        matplotlib.use("WXAgg")
        from matplotlib import pyplot as plt
        from matplotlib import cm
        from matplotlib.colors import Normalize
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is not installed. Please, install it."))


def get_valid_color(color):
    """Get valid Matplotlib color

    :param str color: input color

    :return str|list: color e.g. blue|[0.0, 0.0, 1.0]
    """
    if ":" in color:
        color = [int(x) for x in color.split(":")]
        if max(color) > 1:
            color[:] = [x / 255 for x in color]
    if not matplotlib.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.".format(color)))
    return color


def lazy_import_scipy():
    """Lazy import scipy modules"""
    global scipy
    global interpn
    try:
        import scipy
        from scipy.interpolate import interpn

        return "scipy"
    except ModuleNotFoundError:
        gs.warning(
            _("Scipy is not installed. Creating scatterplot instead of density plot")
        )
        return "noscipy"


def scatter_plot(X, Y, X_name, Y_name, title, color, marker, dimensions, fontsize):
    """
    Create scatterplot

    :param list X: X values
    :param list Y: Y values
    :param str X_name: label for x-axis
    :param str Y_name: label for y-axis
    :param str title: label for plot title (empty is not title)
    :param str color: color of the dots in the scatterplot
    :param str marker: the mark type for the scatterplot dots
    :param list dimensions: plot dimensions (width, height)
    :param float fontsize: fontsize of all text (tic labes are 1pnt smaller)

    :return print ax, fig
    """

    fig, ax = plt.subplots(figsize=dimensions)
    plt.rcParams["font.size"] = fontsize
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(fontsize - 1)
    ax.scatter(X, Y, color=color, marker=marker)
    plt.xlabel(X_name, fontsize=fontsize)
    plt.ylabel(Y_name, fontsize=fontsize)
    if len(title) != 0:
        plt.title(title)
    return ax, fig


def density_scatter(X, Y, X_name, Y_name, bins, title, marker, dimensions, fontsize):
    """
    Scatter plot colored by 2d histogram

    :param list X: X values
    :param list Y: Y values
    :param str X_name: label for x-axis
    :param str Y_name: label for y-axis
    :param list bins: histogram bin size (x,y)
    :param str title: label for plot title (empty is not title)
    :param str color: color of the dots in the scatterplot
    :param str marker: the mark type for the scatterplot dots
    :param list dimensions: plot dimensions (width, height)
    :param float fontsize: fontsize of all text (tic labes are 1pnt smaller)

    :return print ax, fig
    """

    fig, ax = plt.subplots(figsize=dimensions)
    plt.rcParams["font.size"] = fontsize
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(fontsize - 1)
    data, x_e, y_e = np.histogram2d(X, Y, bins=bins, density=False)
    z = interpn(
        (0.5 * (x_e[1:] + x_e[:-1]), 0.5 * (y_e[1:] + y_e[:-1])),
        data,
        np.vstack([X, Y]).T,
        method="splinef2d",
        bounds_error=False,
    )

    # To be sure to plot all data
    z[np.where(np.isnan(z))] = 0.0

    # Sort the points by density, so that the densest points are plotted last
    idx = z.argsort()
    x, y, z = np.array(X)[idx], np.array(Y)[idx], z[idx]

    ax.scatter(x, y, c=z, marker=marker)
    plt.xlabel(X_name, fontsize=fontsize)
    plt.ylabel(Y_name, fontsize=fontsize)
    if len(title) != 0:
        plt.title(title)

    norm = Normalize(vmin=np.min(z), vmax=np.max(z))
    cbar = fig.colorbar(cm.ScalarMappable(norm=norm))
    cbar.ax.set_ylabel("Number of points per bin")
    return ax, fig


def main(options, flags):
    """
    Draws the scatterplot based on the values in two columns.
    Optionally, color the dots according to their density
    """

    # lazy import matplotlib
    lazy_import_matplotlib()
    if options["type"] == "density":
        has_scipy = lazy_import_scipy()
        if has_scipy == "noscipy":
            options["type"] = "scatter"

    # Extract the column values and labels
    columns = "{},{}".format(options["x"], options["y"])
    df = gs.read_command(
        "v.db.select",
        map=options["map"],
        columns=columns,
        where="{} != '' AND {} != ''".format(options["x"], options["y"]),
    ).splitlines()
    X_name, Y_name = df[0].split("|")
    X = [float(i.split("|")[0]) for i in df[1:]]
    Y = [float(j.split("|")[1]) for j in df[1:]]

    # Plot parameters & aesthetics
    plot_dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    plot_title = options["title"]
    file_name = options["file_name"]
    bins = [int(x) for x in options["bins"].split(",")]
    dot_color = get_valid_color(options["color"])
    line_color = get_valid_color(options["line_color"])
    line_style = options["line_style"]
    line_width = options["line_width"]
    dot_marker = options["marker"]

    # Plot scatterplot
    if options["type"] == "scatter":
        ax, p = scatter_plot(
            X=X,
            Y=Y,
            X_name=X_name,
            Y_name=Y_name,
            title=plot_title,
            color=dot_color,
            marker=dot_marker,
            dimensions=plot_dimensions,
            fontsize=float(options["fontsize"]),
        )
    # Plot density plot
    else:
        ax, p = density_scatter(
            X=X,
            Y=Y,
            X_name=X_name,
            Y_name=Y_name,
            bins=bins,
            title=plot_title,
            marker=dot_marker,
            dimensions=plot_dimensions,
            fontsize=float(options["fontsize"]),
        )

    if options["trendline"] == "linear":
        degree = 1
        if int(options["degree"]) != "1":
            gs.message("You opted to add a linear trendline.")
            gs.message(
                "You selected a degree of {}. This will be ignored".format(
                    options["degree"]
                )
            )
    else:
        degree = int(options["degree"])

    if len(options["trendline"]) != 0:
        # Create polynomial model
        trend_model = Polynomial.fit(X, Y, deg=degree)

        # Compute R2 score
        y_predict = trend_model(np.array(X))
        mean_y = np.mean(Y)
        numerator = np.sum((Y - y_predict) ** 2)
        denominator = np.sum((Y - mean_y) ** 2)
        R2 = 1 - (numerator / denominator)
        gs.message(
            "The R2 for the {} trendline(degree={}) is {}".format(
                options["trendline"], degree, round(R2, 3)
            )
        )

        # Plot trend line
        xx, yy = trend_model.linspace()
        ax.plot(
            xx,
            yy,
            color=line_color,
            linestyle=line_style,
            linewidth=line_width,
        )

    if bool(file_name):
        file_name = file_name
        p.savefig(file_name, bbox_inches="tight", dpi=float(options["dpi"]))
    else:
        # Closing message
        gs.message(
            _("\nNote, you need to close the figure \nto finish the script \n\n")
        )
        # Print figure to screen
        p.tight_layout()
        plt.show()


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
