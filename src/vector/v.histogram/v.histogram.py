#!/usr/bin/env python
############################################################################
#
# MODULE:       v.histogram
# AUTHOR:       Moritz Lennert
# PURPOSE:      Draws the histogram of values in a vector attribute column
#
# COPYRIGHT:    (c) 2017-2026 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws the histogram of values in a vector attribute column
# % keyword: display
# % keyword: vector
# % keyword: plot
# % keyword: histogram
# %end

# %option G_OPT_V_MAP
# % guisection: Input
# %end

# %option G_OPT_V_FIELD
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: column
# % description: Attribute column to create histogram from
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_DB_WHERE
# % guisection: Input
# %end

# %option
# % key: bins
# % type: integer
# % description: Number of bins in histogram
# % answer: 30
# % required: no
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key: plot_output
# % label: Name for graphic output file for plot (extension decides format, - for screen)
# % required: yes
# % answer: -
# % guisection: Output
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions
# % description: Dimensions (width,height) of the figure in inches
# % required: no
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Resolution of plot
# % answer: 100
# % required: no
# % guisection: Output
# %end

# %option
# % key: fontsize
# % type: integer
# % label: Font size
# % description: Default font size
# % answer: 10
# % required: no
# % guisection: Output
# %end

# %option
# % key: style
# % type: string
# % label: Matplotlib style
# % description: Matplotlib style sheet, see https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
# % required: no
# % guisection: Plot format
# %end

# %flag
# % key: h
# % label: Horizontal histogram
# % description: Draw the histogram horizontal
# % guisection: Plot format
# %end

# %flag
# % key: r
# % label: Rotate labels
# % description: Rotate the value-axis labels
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
# % description: min and max value of the value axis (x-axis, or y-axis if -h flag is set)
# % required: no
# % guisection: Plot format
# %end

# %option G_OPT_CN
# % key: color
# % label: Color of the bars
# % description: Fill color of the histogram bars. Defaults to the style palette. See manual for color notation.
# % required: no
# % answer:
# % guisection: Histogram format
# %end

# %option G_OPT_CN
# % key: border_color
# % label: Color of the bar borders
# % description: Color of the histogram bar borders. Defaults to the Matplotlib default.
# % required: no
# % answer:
# % guisection: Histogram format
# %end

# %option
# % key: line_width
# % type: double
# % label: Border line width
# % description: Line width of the bar borders. Defaults to the Matplotlib default.
# % required: no
# % guisection: Histogram format
# %end

# %option
# % key: rwidth
# % type: double
# % label: Relative bar width
# % description: Width of the bars as a fraction of the bin width (0.1,1]
# % required: no
# % options: 0.1-1
# % guisection: Histogram format
# %end


import sys
import grass.script as gs


def lazy_import_py_modules():
    """Lazy import Py modules"""
    global mpl
    global plt

    # lazy import matplotlib
    try:
        import matplotlib as mpl

        mpl.use("WXAgg")
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is not installed. Please, install it."))


def apply_style(style):
    """Apply a Matplotlib style sheet, validating the name.

    :param str style: name of a Matplotlib style sheet
    """
    if style:
        if style not in plt.style.available:
            gs.fatal(
                _("Unknown style '{}'. Available styles: {}").format(
                    style, ", ".join(plt.style.available)
                )
            )
        plt.style.use(style)


def get_valid_color(color):
    """Get valid Matplotlib color

    :param str color: input color

    :return str|list: color e.g. blue|[0.0, 0.0, 1.0]
    """
    if ":" in color:
        color = [int(x) / 255 for x in color.split(":")]
    if not mpl.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.").format(color))
    return color


def main():
    # lazy import matplotlib
    lazy_import_py_modules()
    apply_style(options["style"])

    # Input
    vector = options["map"]
    layer = options["layer"]
    column = options["column"]
    bins = int(options["bins"])
    plot_output = options["plot_output"]
    where = options["where"] if options["where"] else None

    # Output options
    dpi = float(options["dpi"])
    if options["plot_dimensions"]:
        dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    else:
        dimensions = [6, 4] if flags["h"] else [4, 6]
    if options["fontsize"]:
        plt.rcParams["font.size"] = int(options["fontsize"])

    # Histogram format options. Only options that were set are passed on, so
    # unset options fall back to the Matplotlib/style defaults.
    fill_color = get_valid_color(options["color"]) if options["color"] else None
    border_color = (
        get_valid_color(options["border_color"]) if options["border_color"] else None
    )
    line_width = float(options["line_width"]) if options["line_width"] else None
    rwidth = float(options["rwidth"]) if options["rwidth"] else None
    horizontal = flags["h"]

    # Read the data
    data = [
        float(x)
        for x in gs.read_command(
            "v.db.select",
            map_=vector,
            layer=layer,
            column=column,
            where=where,
            flags="c",
        ).splitlines()
    ]
    if not data:
        gs.fatal(_("No non-NULL values found for column <{}>.").format(column))

    # Draw the histogram
    fig, ax = plt.subplots(figsize=dimensions, dpi=dpi)
    hist_kwargs = {
        "bins": bins,
        "orientation": "horizontal" if horizontal else "vertical",
    }
    if fill_color is not None:
        hist_kwargs["color"] = fill_color
    if border_color is not None:
        hist_kwargs["edgecolor"] = border_color
    if line_width is not None:
        hist_kwargs["linewidth"] = line_width
    if rwidth is not None:
        hist_kwargs["rwidth"] = rwidth
    ax.hist(data, **hist_kwargs)

    # Axis labels (value axis is x when vertical, y when horizontal)
    if horizontal:
        ax.set_ylabel(column)
        ax.set_xlabel(_("Count"))
    else:
        ax.set_xlabel(column)
        ax.set_ylabel(_("Count"))

    # Rotate the value-axis tick labels
    if flags["r"]:
        ax.tick_params(axis="y" if horizontal else "x", labelrotation=45)

    # Limit the value axis
    if options["axis_limits"]:
        minlim, maxlim = map(float, options["axis_limits"].split(","))
        if horizontal:
            ax.set_ylim([minlim, maxlim])
        else:
            ax.set_xlim([minlim, maxlim])

    # Grid on the count axis
    if flags["g"]:
        if horizontal:
            ax.xaxis.grid(True, alpha=0.5)
        else:
            ax.yaxis.grid(True, alpha=0.5)

    plt.tight_layout()
    if plot_output == "-":
        plt.show()
    else:
        plt.savefig(plot_output)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
