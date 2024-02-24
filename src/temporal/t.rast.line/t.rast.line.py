#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.rast.line
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws a line diagram with lines showing the average values
#               for categories in a user-defined category layer over time.
#               based on the raster layers in a space time raster database.
#
# COPYRIGHT:    (c) 2024 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws line plots of the raster maps in a space-time raster dataset
# % keyword: display
# % keyword: raster
# % keyword: plot
# % keyword: boxplot
# % keyword: statistics
# %end

# %option G_OPT_STRDS_INPUT
# % description: input space-time raster dataset
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_R_MAP
# % key: zones
# % label: Zonal raster
# % description: categorical map with zones
# % required: no
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % key_desc: File name
# % label: Name of output image file
# % required: no
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Resolution of plot
# % required: no
# % guisection: Output
# %end

# %option
# % key: stddev
# % type: double
# % label: stddev
# % description: Width of error bar in terms of number of standard deviations.
# % required: no
# % guisection: Statistics
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions (width,height)
# % description: Dimensions (width,height) of the figure in inches
# % required: no
# % guisection: Plot format
# %end

# %option
# % type: double
# % options: -90-90
# % key: rotate_labels
# % label: Rotate labels
# % description: Rotate labels (degrees)
# % guisection: Plot format
# %end

# %flag
# % key: g
# % label: Add grid lines
# % description: Add grid lines
# % guisection: Plot format
# %end

# %option
# % key: font_size
# % type: integer
# % label: Font size
# % description: Font size of labels
# % guisection: Plot format
# % answer: 10
# % required: no
# %end

# %option
# % key: date_format
# % type: string
# % label: Date format
# % description: Set date format (see https://strftime.org/ for options)
# % guisection: Plot format
# % required: no
# %end

# %flag
# % key: d
# % label: ConciseDateFormatter
# % description: Us date format as compact as possible while still having complete date information. This will override the data_format setting.
# % guisection: Plot format
# %end

# %option
# % key: axis_limits
# % type: string
# % label: limit value axis
# % description: min and max value of y-axis, or x-axis if -h flag is set)
# % guisection: Plot format
# % required: no
# %end

# %option
# % key: line_width
# % type: double
# % label: Line width
# % description: The width of the line(s)
# % required: no
# % answer: 1
# % guisection: Line format
# %end

# %options G_OPT_CN
# % key: line_color
# % type: string
# % label: Line color
# % description: Color of the line. See manual page for color notation options. Cannot be used together with the zonal raster.
# % required: no
# % answer: blue
# % guisection: Line format
# %end

# %rules
# % exclusive: line_color, zones
# %end

# %option
# % key: alpha
# % type: double
# % description: Transparency of the error band
# % required: no
# % options: 0-1
# % answer: 0.2
# % guisection: Plot format
# %end

# %option G_OPT_M_NPROCS
# % key: nprocs
# % label: Number of processor threads to use.
# % answer: 1
# %end

import atexit
import sys
from datetime import datetime
from dateutil import parser
import grass.script as gs


def lazy_import_py_modules():
    """Lazy import Py modules"""
    global matplotlib
    global plt

    # lazy import matplotlib
    try:
        import matplotlib

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


def check_integer(name):
    """Check if map values are integer

    :param str name: name zonal map

    :return str: no return if map is of type integer, otherwise error message
    """
    input_info = gs.raster_info(name)
    if input_info["datatype"] != "CELL":
        gs.fatal(_("The zonal raster must be of type CELL (integer)"))


def get_categories(zones):
    """Get list of categories and IDs of cover layer"""

    cats = gs.read_command("r.category", map=zones, separator="pipe").split("\n")
    cats = [_f for _f in cats if _f]
    cats_ids = [int(x.split("|")[0]) for x in cats]
    cats_names = [x.split("|")[1] for x in cats]
    for id, name in enumerate(cats_names):
        if len(name) == 0:
            cats_names[id] = cats_ids[id]
    return [cats_ids, cats_names]


def line_stats(strds, coverlayer, cats_ids, stddev, threads):
    """Compute line statistics

    :param str strds: name of input strds
    :param str coverlayer: name of cover layer
    :param float stddev: width of c.i. in stddev
    :param int threads: number of threads

    :return list: list with dates, mean value and upper and lower limit of c.i.
    """
    # Get type
    t_info = gs.parse_command("t.info", flags="g", input=strds)
    map_time = t_info["map_time"]
    temp_type = t_info["temporal_type"]

    # Get stats
    univar = gs.read_command(
        "t.rast.univar", input=strds, zones=coverlayer, nproc=threads
    ).split("\n")
    univar = [_f for _f in univar if _f]
    univar = [x.split("|") for x in univar]

    # Get positions
    idx_start = [idx for idx, name in enumerate(univar[0]) if name == "start"][0]
    idx_end = [idx for idx, name in enumerate(univar[0]) if name == "end"][0]
    idx_mean = [idx for idx, name in enumerate(univar[0]) if name == "mean"][0]
    idx_stddev = [idx for idx, name in enumerate(univar[0]) if name == "stddev"][0]

    # Get date time and values
    mean_vals = list()
    upper_limit_vals = list()
    lower_limit_vals = list()
    if bool(coverlayer):
        idx_zone = [idx for idx, name in enumerate(univar[0]) if name == "zone"][0]
        if temp_type == "absolute":
            if not bool(idx_end):
                date_points = [
                    datetime.strptime(x[idx_start], "%Y-%m-%d %H:%M:%S")
                    for x in univar[1:]
                    if int(x[idx_zone]) == cats_ids[0]
                ]
            else:
                date_start = [
                    int(
                        datetime.strptime(x[idx_start], "%Y-%m-%d %H:%M:%S").strftime(
                            "%s"
                        )
                    )
                    for x in univar[1:]
                    if int(x[idx_zone]) == cats_ids[0]
                ]
                date_end = [
                    int(
                        datetime.strptime(x[idx_end], "%Y-%m-%d %H:%M:%S").strftime(
                            "%s"
                        )
                    )
                    for x in univar[1:]
                    if int(x[idx_zone]) == cats_ids[0]
                ]
                date_points = [
                    datetime.fromtimestamp(s + (e - s) / 2).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    for s, e in zip(date_start, date_end)
                ]
        else:
            if not bool(idx_end):
                date_points = [
                    int(x[idx_start])
                    for x in univar[1:]
                    if int(x[idx_zone]) == cats_ids[0]
                ]
            else:
                date_start = [
                    int(x[idx_start])
                    for x in univar[1:]
                    if int(x[idx_zone]) == cats_ids[0]
                ]
                date_end = [
                    int(x[idx_end])
                    for x in univar[1:]
                    if int(x[idx_zone]) == cats_ids[0]
                ]
                date_points = [s + (e - s) / 2 for s, e in zip(date_start, date_end)]
        for i, n in enumerate(cats_ids):
            m = [
                float(x[idx_mean])
                for x in univar[1:]
                if int(x[idx_zone]) == cats_ids[i]
            ]
            s = [
                float(x[idx_stddev])
                for x in univar[1:]
                if int(x[idx_zone]) == cats_ids[i]
            ]
            upper_limit_vals.append([m + s * stddev for m, s in zip(m, s)])
            lower_limit_vals.append([m - s * stddev for m, s in zip(m, s)])
            mean_vals.append(m)
    else:
        if temp_type == "absolute":
            if not bool(idx_end):
                date_points = [
                    datetime.strptime(x[idx_start], "%Y-%m-%d %H:%M:%S")
                    for x in univar[1:]
                ]
            else:
                date_start = [
                    int(
                        datetime.strptime(x[idx_start], "%Y-%m-%d %H:%M:%S").strftime(
                            "%s"
                        )
                    )
                    for x in univar[1:]
                ]
                date_end = [
                    int(
                        datetime.strptime(x[idx_end], "%Y-%m-%d %H:%M:%S").strftime(
                            "%s"
                        )
                    )
                    for x in univar[1:]
                ]
                date_points = [
                    datetime.fromtimestamp(s + (e - s) / 2).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    for s, e in zip(date_start, date_end)
                ]
        else:
            if not bool(idx_end):
                date_points = [int(x[idx_start]) for x in univar[1:]]
            else:
                date_start = [int(x[idx_start]) for x in univar[1:]]
                date_end = [int(x[idx_end]) for x in univar[1:]]
                date_points = [s + (e - s) / 2 for s, e in zip(date_start, date_end)]
        m = [float(x[idx_mean]) for x in univar[1:]]
        s = [float(x[idx_stddev]) for x in univar[1:]]
        upper_limit_vals[0] = [m + s * stddev for m, s in zip(m, s)]
        lower_limit_vals[0] = [m - s * stddev for m, s in zip(m, s)]
        mean_vals.append(m)

    # Return values
    return [date_points, mean_vals, upper_limit_vals, lower_limit_vals]


def get_raster_colors(raster, cats_ids):
    """Get colors of cover layer"""
    cz = gs.read_command("r.colors.out", map=raster).split("\n")
    cz = [_f for _f in cz if _f]
    cz = [x.split(" ") for x in cz]
    cz = [get_valid_color(x[1]) for x in cz if x[0] in str(cats_ids)]
    return cz


def set_axis(ax, date_format, temp_unit, vertical, rast_dates, temp_lngt):
    """Define granuality and format x (or y) axis

    :param str date_format: user defined date format
    :param str temp_unit: temporal granuality of strds
    :param bool vertical: orientation boxplots
    :param list rast_dates: list with dates of input rasters
    :param float temp_lngt: temporal resolution (in time_unit units)
    """

    if "year" in temp_unit:
        if bool(date_format):
            date_fmt = mdates.DateFormatter(date_format)
        else:
            date_fmt = mdates.DateFormatter("%Y")
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
        else:
            ax.yaxis.set_major_formatter(date_fmt)
    if "month" in temp_unit:
        if bool(date_format):
            date_fmt = mdates.DateFormatter(date_format)
        else:
            date_fmt = mdates.DateFormatter("%Y-%m")
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
        else:
            ax.yaxis.set_major_formatter(date_fmt)
    if "day" in temp_unit:
        if bool(date_format):
            date_fmt = mdates.DateFormatter(date_format)
        else:
            date_fmt = mdates.DateFormatter("%Y-%m-%d")
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
        else:
            ax.yaxis.set_major_formatter(date_fmt)
    if "hour" in temp_unit:
        if bool(date_format):
            date_fmt = mdates.DateFormatter(date_format)
        else:
            date_fmt = mdates.DateFormatter("hour %H")
        start_time = (
            mdates.date2num(parser.parse(timestr=rast_dates[0])) - 1 / 48 * temp_lngt
        )
        end_time = (
            mdates.date2num(parser.parse(timestr=rast_dates[-1])) + 1 / 48 * temp_lngt
        )
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
            ax.set_xlim(mdates.num2date(start_time), mdates.num2date(end_time))
        else:
            ax.yaxis.set_major_formatter(date_fmt)
            ax.set_ylim(mdates.num2date(start_time), mdates.num2date(end_time))
    if "minute" in temp_unit:
        if bool(date_format):
            date_fmt = mdates.DateFormatter(date_format)
        else:
            date_fmt = mdates.DateFormatter("min. %M")
        start_time = (
            mdates.date2num(parser.parse(timestr=rast_dates[0])) - 1 / 2880 * temp_lngt
        )
        end_time = (
            mdates.date2num(parser.parse(timestr=rast_dates[-1])) + 1 / 2880 * temp_lngt
        )
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
            ax.set_xlim(mdates.num2date(start_time), mdates.num2date(end_time))
        else:
            ax.yaxis.set_major_formatter(date_fmt)
            ax.set_ylim(mdates.num2date(start_time), mdates.num2date(end_time))
    if "second" in temp_unit:
        if bool(date_format):
            date_fmt = mdates.DateFormatter(date_format)
        else:
            date_fmt = mdates.DateFormatter("sec. %S")
        start_time = (
            mdates.date2num(parser.parse(timestr=rast_dates[0]))
            - 1 / 172800 * temp_lngt
        )
        end_time = (
            mdates.date2num(parser.parse(timestr=rast_dates[-1]))
            + 1 / 172800 * temp_lngt
        )
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
            ax.set_xlim(mdates.num2date(start_time), mdates.num2date(end_time))
        else:
            ax.yaxis.set_major_formatter(date_fmt)
            ax.set_ylim(mdates.num2date(start_time), mdates.num2date(end_time))
    return ax


def main(options, flags):
    """
    Draws the boxplot of raster values. Optionally, this is done per
    category of a zonal raster layer
    """

    # lazy import matplotlib
    lazy_import_py_modules()

    # Get cover cateogory IDs and colors
    if bool(options["zones"]):
        check_integer(options["zones"])
        cats_ids, cats_names = get_categories(options["zones"])
        line_colors = get_raster_colors(options["zones"], cats_ids)
    else:
        line_colors = get_valid_color(options["line_color"])

    # Get stats
    x, y_mean, y_ul, y_ll = line_stats(
        strds=options["input"],
        coverlayer=options["zones"],
        cats_ids=cats_ids,
        stddev=float(options["stddev"]),
        threads=int(options["nprocs"]),
    )

    # Plot format options
    plt.rcParams["font.size"] = int(options["font_size"])
    grid = flags["g"]
    if bool(options["line_width"]):
        line_width = float(options["line_width"])

    # Output options
    output = options["output"]
    if bool(options["dpi"]):
        dpi = float(options["dpi"])
    else:
        dpi = 300
    if options["plot_dimensions"]:
        dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    else:
        dimensions = [6, 4]

    # Plot the figure
    _, ax = plt.subplots(figsize=dimensions)
    for i, _ in enumerate(cats_ids):
        ax.plot(x, y_mean[i], label=cats_names[i], color=line_colors[i])
        ax.fill_between(
            x, y_ll[i], y_ul[i], color=line_colors[i], alpha=float(options["alpha"])
        )

    # Label orientation
    if bool(options["rotate_labels"]):
        rotate_labels = float(options["rotate_labels"])
        if abs(rotate_labels) <= 10 or abs(rotate_labels) >= 80:
            plt.xticks(rotation=rotate_labels)
        elif rotate_labels < 0:
            plt.xticks(rotation=rotate_labels, ha="left", rotation_mode="anchor")
        else:
            plt.xticks(rotation=rotate_labels, ha="right", rotation_mode="anchor")

    # Set limits value axis
    if bool(options["axis_limits"]):
        minlim, maxlim = map(float, options["axis_limits"].split(","))
        if bool(vertical):
            plt.ylim([minlim, maxlim])
        else:
            plt.xlim([minlim, maxlim])

    # Set grid (optional)
    ax.xaxis.grid(bool(grid))

    # Print to file (optional)
    if output:
        plt.savefig(output, bbox_inches="tight", dpi=dpi)
        plt.close()
    else:
        plt.tight_layout()
        plt.show()
        plt.close()


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
