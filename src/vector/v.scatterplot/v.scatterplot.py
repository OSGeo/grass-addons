#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.scatterplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Plots the values of two columns in the attribute table
#               of an input vector layer in a scatterplot.
#
# COPYRIGHT:    (c) 2023-2024 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Plots the values of two columns in the attribute table of an input vector layer in a scatterplot.
# % keyword: vector
# % keyword: plot
# % keyword: scatterplot
# %end

# %option G_OPT_V_MAP
# % label: Input map
# % description: input vector layer
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: x
# % label: Name of x column
# % description: Name of the column with x values
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: y
# % label: Name of y column
# % description: Name of the column with y values
# % required: yes
# % guisection: Input
# %end

# %option
# % key: type
# % type: string
# % label: Plot type
# % description: Type of plot (scatter, density)
# % required: no
# % answer: scatter
# % options: scatter, density
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % label: Name of the output file (extension decides format)
# % description: Name of the output file. The format is determined by the file extension.
# % required: no
# % guisection: Output
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions (width,height)
# % description: Dimensions (width,height) of the figure in inches
# % required: no
# % answer: 6.4,4.8
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Resolution of plot in dpi's
# % required: no
# % answer: 100
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
# % key: fontsize
# % type: double
# % label: Font size
# % answer: 10
# % description: The basis font size (default = 10)
# % guisection: Aesthetics
# % required: no
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

# %option
# % key: s
# % type: double
# % label: Marker size
# % description: Set marker size
# % required: no
# % guisection: Aesthetics
# %end

# %option G_OPT_C
# % key: color
# % type: string
# % label: Dot color
# % description: Color of dots
# % required: no
# % guisection: Aesthetics
# %end

# %option G_OPT_DB_COLUMN
# % key: rgbcolumn
# % type: string
# % label: RGB column
# % description: Column with RGB values defining the colors of the dots of the scatterplot
# % required: no
# % guisection: Aesthetics
# %end

# %rules
# % exclusive: color,rgbcolumn
# %end

# %option
# % key: bins
# % type: string
# % label: 2D bins
# % description: The number of bins in x and y dimension. Density is expressed as the number of points falling within the x and y boundaries of a bin.
# % required: no
# % answer: 30,30
# % guisection: Density
# %end

# %option
# % key: density_colormap
# % type: string
# % label: Density plot color map
# % description: Select the color map to be used for the density scatter plot
# % required: no
# % answer: viridis
# % options: viridis,plasma,inferno,magma,cividis,Greys,Purples,Blues,Greens,Oranges,Reds,YlOrBr,YlOrRd,OrRd,PuRd,RdPu,BuPu,GnBu,PuBu,YlGnBu,PuBuGn,BuGn,YlGn
# % guisection: Density
# %end

# % flag
# % key: r
# % description: Reverse color map
# % guisection: Density
# % end

# %option
# % key: trendline
# % type: string
# % label: Trendline
# % description: Plot trendline
# % required: no
# % options: linear, polynomial
# % guisection: Trendline
# %end

# %option
# % key: degree
# % type: integer
# % label: Degree
# % description: Degree polynomial trendline
# % required: no
# % answer: 1
# % guisection: Trendline
# %end

# %option G_OPT_C
# % key: line_color
# % type: string
# % label: Color trendline
# % description: Color of the trendline
# % required: no
# % answer: darkgrey
# % guisection: Trendline
# %end

# %option
# % key: line_style
# % type: string
# % label: Line style trendline
# % description: Line style trendline
# % required: no
# % answer: --
# % guisection: Trendline
# %end

# %option
# % key: line_width
# % type: double
# % label: trendline width
# % description: Line width of the trendline
# % required: no
# % answer: 2
# % guisection: Trendline
# %end

# % flag
# % key: e
# % description: Draw a covariance confidence ellipse(s)
# % guisection: Ellipse
# % end

# %option
# % key: n
# % type: string
# % label: standard deviations
# % description: Draw the covariance confidence ellipse(s) with radius of n standard deviations.
# % answer: 2
# % guisection: Ellipse
# %end

# %option G_OPT_C
# % key: ellipse_color
# % type: string
# % label: Ellipse color
# % description: Color of the ellipse
# % required: no
# % answer: red
# % guisection: Ellipse
# %end

# %option
# % key: ellipse_alpha
# % type: double
# % label: Opacity ellipse fill.
# % description: Opacity of the fill color of the ellipse.
# % required: no
# % answer: 0.1
# % options: 0-1
# % guisection: Ellipse
# %end

# %option
# % key: ellipse_edge_style
# % type: string
# % label: Ellipse edge style
# % description: Line style of the ellipse
# % required: no
# % answer: -
# % guisection: Ellipse
# %end

# %option
# % key: ellipse_edge_width
# % type: double
# % label: Ellipse edge width
# % description: Width of the ellipse edge
# % required: no
# % answer: 1.5
# % guisection: Ellipse
# %end

# %option G_OPT_DB_COLUMN
# % key: groups
# % type: string
# % label: Column grouping the features in categories
# % description: Colum with categories. If selected, a separate ellipse will be drawn for each group/category
# % guisection: Ellipse
# %end

# %option G_OPT_DB_COLUMN
# % key: groups_rgb
# % type: string
# % label: RGB column for ellipse categories
# % description: Column with RGB values per category. These will be used to define the color of the ellipse.
# % required: no
# % guisection: Ellipse
# %end

# %option
# % key: ellipse_legend
# % type: string
# % label: legend for ellipses
# % description: Print the legend for the ellipses (only for if ellipses for groups are drawn)
# % required: no
# % answer: yes
# % options: yes,no
# % guisection: Ellipse
# %end

# %option
# % key: quadrants
# % type: string
# % label: quadrants
# % description: Print the mean or median on x and y-axis
# % required: no
# % options: mean,median
# % guisection: Quadrants
# %end

# %option G_OPT_C
# % key: quandrant_linecolor
# % type: string
# % label: Line color
# % description: Color of the lines making up the quadrants
# % required: no
# % answer: grey
# % guisection: Quadrants
# %end

# %option
# % key: quandrant_linewidth
# % type: double
# % label: quandrant line width
# % description: Line width of the lines dividing the points in four quadrants.
# % required: no
# % answer: 1
# % guisection: Quadrants
# %end

# %rules
# % requires: groups_rgb,groups
# %end

# %rules
# % requires: ellipse_legend,groups
# %end

# %flag
# % key: g
# % label: Add grid lines
# % description: Add grid lines.
# % guisection: Aesthetics
# %end

# %rules
# % excludes: quadrants,-g
# %end


# %option
# % key: x_axis_limits
# % type: string
# % label: X axis range (min,max)
# % description: Set the X axis range to be displayed
# % required: no
# %end

# %option
# % key: y_axis_limits
# % type: string
# % label: Y axis range (min,max)
# % description: Set the Y axis range to be displayed
# % required: no
# %end

import atexit
import sys
import uuid
import numpy as np
from subprocess import PIPE
import grass.script as gs
from grass.pygrass.modules import Module
from numpy.polynomial import Polynomial
import random


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

    :return list: rgba list, e.g. [0.0, 0.0, 1.0, 1]
    """
    if ":" in color:
        color = [int(x) for x in color.split(":")]
        if max(color) > 1:
            color[:] = [x / 255 for x in color]
    if not matplotlib.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.".format(color)))
    color = matplotlib.colors.to_rgba(color)
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


def scatter_plot(X, Y, X_name, Y_name, title, color, marker, s, dimensions, fontsize):
    """
    Create scatterplot

    :param list X: X values
    :param list Y: Y values
    :param str X_name: label for x-axis
    :param str Y_name: label for y-axis
    :param str title: label for plot title (empty is not title)
    :param str color: color of the dots in the scatterplot
    :param str marker: the mark type for the scatterplot dots
    :param float s: size of marker
    :param list dimensions: plot dimensions (width, height)
    :param float fontsize: fontsize of all text (tic labes are 1pnt smaller)

    :return print ax, fig
    """

    fig, ax = plt.subplots(figsize=dimensions)
    plt.rcParams["font.size"] = fontsize
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(fontsize - 1)
    if s:
        ax.scatter(X, Y, color=color, marker=marker, s=s)
    else:
        ax.scatter(X, Y, color=color, marker=marker)
    plt.xlabel(X_name, fontsize=fontsize)
    plt.ylabel(Y_name, fontsize=fontsize)
    if len(title) != 0:
        plt.title(title)
    return ax, fig


def density_scatter(
    X,
    Y,
    X_name,
    Y_name,
    bins,
    title,
    marker,
    s,
    dimensions,
    fontsize,
    density_colormap,
    reverse_colors,
):
    """
    Scatter plot colored by 2d histogram

    :param list X: X values
    :param list Y: Y values
    :param str X_name: label for x-axis
    :param str Y_name: label for y-axis
    :param list bins: histogram bin size (x,y)
    :param str title: label for plot title (empty is not title)
    :param str marker: the mark type for the scatterplot dots
    :param float s: size of marker
    :param list dimensions: plot dimensions (width, height)
    :param float fontsize: fontsize of all text (tic labes are 1pnt smaller)
    :param str density_colormap: the name of the color map to be used
    :param bool reverse_colors: true means the color map will be reversed

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

    cmap = matplotlib.cm.get_cmap(density_colormap)
    if reverse_colors:
        cmap = cmap.reversed()
    if s:
        ax.scatter(x, y, c=z, s=s, marker=marker, cmap=cmap)
    else:
        ax.scatter(x, y, c=z, marker=marker, cmap=cmap)
    plt.xlabel(X_name, fontsize=fontsize)
    plt.ylabel(Y_name, fontsize=fontsize)
    if len(title) != 0:
        plt.title(title)

    # Create a ScalarMappable for the colorbar
    # Set an empty array to allow the ScalarMappable to be used for the legend
    norm = Normalize(vmin=np.min(z), vmax=np.max(z))
    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # Add colorbar to the right of the plo
    cbar = fig.colorbar(sm, ax=ax)
    cbar.ax.set_ylabel("Number of points per bin")
    return ax, fig


def confidence_ellipse(x, y, ax, n, facecolor="none", **kwargs):
    """
    Create a plot of the covariance confidence ellipse of *x* and *y*.

    :param array x: input data x-axis.
    :param array y: input data y-axis.
    :param matplotlib.axes.Axes ax: The axes object to draw the ellipse into.
    :param float n: The number of standard deviations or errors to determine the ellipse's radiuses.

    :return matplotlib.patches.Ellipse
    """
    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensional dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = matplotlib.patches.Ellipse(
        (0, 0),
        width=ell_radius_x * 2,
        height=ell_radius_y * 2,
        facecolor=facecolor,
        **kwargs,
    )

    # Calculating the standard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n
    mean_x = np.mean(x)

    # calculating the standard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n
    mean_y = np.mean(y)

    transf = (
        matplotlib.transforms.Affine2D()
        .rotate_deg(45)
        .scale(scale_x, scale_y)
        .translate(mean_x, mean_y)
    )

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)


def random_color():
    """
    Function to generate a random color

    :return list with rgb elements
    """
    hex_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    return matplotlib.colors.hex2color(hex_color)


def main(options, flags):
    """
    Draws the scatterplot based on the values in two columns.
    Optionally, color the dots according to their density
    """

    # lazy import modules
    lazy_import_matplotlib()
    if options["type"] == "density":
        has_scipy = lazy_import_scipy()
        if has_scipy == "noscipy":
            options["type"] = "scatter"

    # Extract the column values and labels for x and y columns
    columns = "{},{}".format(options["x"], options["y"])
    sql_stat = "{} != '' AND {} != ''".format(options["x"], options["y"])
    if options["rgbcolumn"]:
        columns = "{},{}".format(columns, options["rgbcolumn"])
        sql_stat = "{} AND {} != ''".format(sql_stat, options["rgbcolumn"])
    if options["groups"]:
        columns = "{},{}".format(columns, options["groups"])
        sql_stat = "{} AND {} != ''".format(sql_stat, options["groups"])
    if options["groups_rgb"]:
        columns = "{},{}".format(columns, options["groups_rgb"])
        sql_stat = "{} AND {} != ''".format(sql_stat, options["groups_rgb"])
    df = gs.read_command(
        "v.db.select",
        map=options["map"],
        columns=columns,
        where=sql_stat,
    ).splitlines()
    X_name, Y_name = df[0].split("|")[0:2]
    X = [float(i.split("|")[0]) for i in df[1:]]
    Y = [float(j.split("|")[1]) for j in df[1:]]
    n = 2
    if options["rgbcolumn"]:
        rgbcolumn = [get_valid_color(j.split("|")[n]) for j in df[1:]]
        n += 1
    if options["groups"]:
        groups = [j.split("|")[n] for j in df[1:]]
        n += 1
    if options["groups_rgb"]:
        groups_rgb = [get_valid_color(j.split("|")[n]) for j in df[1:]]

    # Plot parameters & aesthetics
    plot_dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    plot_title = options["title"]
    file_name = options["output"]
    bins = [int(x) for x in options["bins"].split(",")]
    if options["rgbcolumn"]:
        dot_color = rgbcolumn
    elif options["color"]:
        dot_color = get_valid_color(options["color"])
    else:
        dot_color = get_valid_color("blue")
    line_color = get_valid_color(options["line_color"])
    line_style = options["line_style"]
    line_width = options["line_width"]
    dot_marker = options["marker"]
    if options["s"]:
        s = float(options["s"])
    else:
        s = False

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
            s=s,
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
            s=s,
            dimensions=plot_dimensions,
            fontsize=float(options["fontsize"]),
            density_colormap=options["density_colormap"],
            reverse_colors=flags["r"],
        )

    # Quadrants
    if options["quadrants"]:
        if options["quadrants"] == "mean":
            X_div = np.mean(X)
            Y_div = np.mean(Y)
        else:
            X_div = np.median(X)
            Y_div = np.median(Y)
        quadrant_color = get_valid_color(options["quandrant_linecolor"])
        quadrant_linewidth = float(options["quandrant_linewidth"])
        ax.axhline(
            y=Y_div, color=quadrant_color, linewidth=quadrant_linewidth, zorder=0
        )
        ax.axvline(
            x=X_div, color=quadrant_color, linewidth=quadrant_linewidth, zorder=0
        )

    # Set grid (optional)
    if flags["g"]:
        ax.set_axisbelow(True)
        ax.xaxis.grid(linewidth=0.5, alpha=0.5)
        ax.yaxis.grid(linewidth=0.5, alpha=0.5)

    # Trendline
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

        gs.message("---------------------------------------")
        gs.message(
            "The R2 for the {} trendline(degree={}) is {}".format(
                options["trendline"], degree, round(R2, 3)
            )
        )
        # Print the regression equation
        coefficients = np.round(trend_model.convert().coef)
        equation = f"Y = {coefficients[degree]:.2f} * X^{degree}"
        for i in range(degree - 1, 0, -1):
            print(i)
            equation += f" + {coefficients[i]:.2f} * X^{i}"
        equation += f" + {coefficients[0]:.2f}"
        gs.message("Trend line Equation:")
        gs.message(equation)
        gs.message("---------------------------------------")

        # Plot trend line
        xx, yy = trend_model.linspace()
        ax.plot(
            xx,
            yy,
            color=line_color,
            linestyle=line_style,
            linewidth=line_width,
        )

    # Plot confidence ellipse based on all data
    if flags["e"]:
        if not options["groups"]:
            edge_color = get_valid_color(options["ellipse_color"])
            edge_width = float(options["ellipse_edge_width"])
            edge_style = options["ellipse_edge_style"]
            face_color = list(edge_color)
            face_color[-1] = float(options["ellipse_alpha"])
            confidence_ellipse(
                X,
                Y,
                ax,
                n=float(options["n"]),
                edgecolor="white",
                linewidth=edge_width * 1.5,
                linestyle=edge_style,
                facecolor="none",
            )
            confidence_ellipse(
                X,
                Y,
                ax,
                n=float(options["n"]),
                edgecolor=edge_color,
                linewidth=edge_width,
                linestyle=edge_style,
                facecolor=face_color,
            )
        else:
            group_names = list(set(groups))
            for group_name in group_names:
                indices = [
                    index for index, value in enumerate(groups) if value == group_name
                ]
                sub_x = [X[i] for i in indices]
                sub_y = [Y[i] for i in indices]
                if options["groups_rgb"]:
                    edge_color = groups_rgb[indices[0]]
                else:
                    edge_color = get_valid_color(random_color())
                edge_width = float(options["ellipse_edge_width"])
                edge_style = options["ellipse_edge_style"]
                face_color = list(edge_color)
                face_color[-1] = float(options["ellipse_alpha"])
                confidence_ellipse(
                    sub_x,
                    sub_y,
                    ax,
                    n=float(options["n"]),
                    edgecolor="white",
                    linewidth=edge_width * 1.8,
                    linestyle="-",
                    facecolor="none",
                )
                confidence_ellipse(
                    sub_x,
                    sub_y,
                    ax,
                    n=float(options["n"]),
                    edgecolor=edge_color,
                    linewidth=edge_width,
                    linestyle=edge_style,
                    facecolor=face_color,
                    label=group_name,
                )
            if options["ellipse_legend"]:
                fontsize = float(options["fontsize"]) * 0.9
                plt.legend(fontsize=fontsize)

    if options["x_axis_limits"]:
        xlim = [float(i) for i in options["x_axis_limits"].split(",")]
        ax.set_xlim(xlim)
    if options["y_axis_limits"]:
        ylim = [float(i) for i in options["y_axis_limits"].split(",")]
        ax.set_ylim(ylim)

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
