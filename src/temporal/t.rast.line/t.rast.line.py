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
# % keyword: line plot
# % keyword: statistics
# %end

# %option G_OPT_STRDS_INPUT
# % description: Input space-time raster dataset.
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_T_WHERE
# % description: WHERE conditions of SQL statement without 'where' keyword used in the temporal GIS framework. Example: start_time > '2001-01-01 12:30:00'
# % guisection: Input
# %end

# %option G_OPT_R_MAP
# % key: zones
# % label: Zonal raster
# % description: Categorical map with zones for which the trend lines need to be drawn.
# % required: no
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % key_desc: File name
# % label: Name of output image file.
# % required: no
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Resolution of plot.
# % required: no
# % guisection: Output
# %end

# %option
# % key: error
# % type: string
# % label: error bar
# % description: Error bar to indicate the error or uncertainty per category. Options are error bar in standard deviations (sd) or standard error (se). Leave empty to ommit the error bar.
# % options: sd,se
# % guisection: Statistics
# %end

# %option
# % key: n
# % type: double
# % label: multiply sd/se
# % description: Width of error bar in terms of number of standard error or standard deviation.
# % required: no
# % guisection: Statistics
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions (width,height)
# % description: Dimensions (width,height) of the figure in inches.
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: rotate_labels
# % type: double
# % options: -90-90
# % label: Rotate labels
# % description: Rotate labels (degrees).
# % guisection: Plot format
# %end

# %flag
# % key: g
# % label: Add grid lines
# % description: Add grid lines.
# % guisection: Plot format
# %end

# %flag
# % key: l
# % label: Legend
# % description: Select this if you want to plot the legend. This only works if a cover layer is provided.
# % guisection: Plot format
# %end

# %rules
# % requires: -l, zones
# %end

# %option
# % key: font_size
# % type: integer
# % label: Font size
# % description: Font size of labels.
# % guisection: Plot format
# % answer: 10
# % required: no
# %end

# %option
# % key: date_interval
# % type: string
# % label: Date interval
# % description: Set interval for plotting of the dates/times
# % options: year,month,week,day,hour,minute
# % guisection: Plot format
# % required: no
# %end

# %option
# % key: date_format
# % type: string
# % label: Date format
# % description: Set date format (see https://strftime.org/ for options).
# % guisection: Plot format
# % required: no
# %end

# %option
# % key: axis_limits
# % type: string
# % label: limit value axis
# % description: min and max value of y-axis, or x-axis if -h flag is set).
# % guisection: Plot format
# % required: no
# %end

# %option
# % key: line_width
# % type: double
# % label: Line width
# % description: The width of the line(s).
# % required: no
# % answer: 1
# % guisection: Plot format
# %end

# %options G_OPT_CN
# % key: line_color
# % type: string
# % label: Line color
# % description: Color of the line. See manual page for color notation options. Cannot be used together with the zonal raster.
# % required: no
# % answer: blue
# % guisection: Plot format
# %end

# %rules
# % exclusive: line_color, zones
# %end

# %option
# % key: alpha
# % type: double
# % description: Transparency of the error band.
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

import sys
from datetime import datetime
from dateutil import parser
import grass.script as gs
from math import sqrt
import matplotlib.dates as mdates


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


def get_rast_name_dates(rasters, col_sep):
    """Create list of names, dates and temporal type
    of raster layers in input strds

    :param str rasters: list with names of the rasters in the input strds
    :param str col_sep: column separator e.g. "2000_01_tempmean|
                                               2000-01-01 00:00:00|absolute"

    :return tuple: tuple with list of dates and names of raster layers in strds
    """
    raster_names = []
    raster_dates = []
    for raster in rasters.splitlines():
        raster_name, raster_date, temp_type = raster.split(col_sep)
        raster_names.append(raster_name)
        raster_dates.append(raster_date)
    return (raster_names, raster_dates)


def check_integer(name):
    """Check if map values are integer

    :param str name: name zonal map

    :return str: no return if map is of type integer, otherwise error message
    """
    input_info = gs.raster_info(name)
    if input_info["datatype"] != "CELL":
        gs.fatal(_("The zonal raster must be of type CELL (integer)"))


def get_categories(coverlayer, zone_cats):
    """Get list of categories and IDs of cover layer

    :param str zones: name of zonal layer

    :return list: Nested list with list of zonal categories and list with labels of categories
    """

    if zone_cats:
        cats = gs.read_command(
            "r.category", map=coverlayer, cats=zone_cats, separator="pipe"
        ).split("\n")
    else:
        cats = gs.read_command("r.category", map=coverlayer, separator="pipe").split(
            "\n"
        )

    cats = [_f for _f in cats if _f]
    cats_ids = [int(x.split("|")[0]) for x in cats]
    cats_names = [x.split("|")[1] for x in cats]
    for id, name in enumerate(cats_names):
        if len(name) == 0:
            cats_names[id] = cats_ids[id]
    return [cats_ids, cats_names]


def line_stats(strds, coverlayer, error, n, threads, temp_type, where):
    """Compute line statistics

    :param str strds: name of input strds
    :param str coverlayer: name of cover layer
    :param str error: Error bar in standard deviations (sd) or standard error (se).
    :param float n: Width of error bar in terms of sd or se
    :param int threads: number of threads
    :param str temp_type: temporal type of the strds

    :return list: list with dates, mean value and upper and lower limit of c.i.
    """
    # Get stats
    univar = gs.read_command(
        "t.rast.univar", input=strds, zones=coverlayer, where=where, nproc=threads
    ).split("\n")
    univar = [_f for _f in univar if _f]
    univar = [x.split("|") for x in univar]

    # Get positions of variables
    idx_start = [idx for idx, name in enumerate(univar[0]) if name == "start"][0]
    idx_end = [idx for idx, name in enumerate(univar[0]) if name == "end"][0]
    idx_mean = [idx for idx, name in enumerate(univar[0]) if name == "mean"][0]
    idx_sd = [idx for idx, name in enumerate(univar[0]) if name == "stddev"][0]
    idx_n = [idx for idx, name in enumerate(univar[0]) if name == "non_null_cells"][0]

    # Get date time and values
    mean_vals = list()
    upper_limit_vals = list()
    lower_limit_vals = list()
    if bool(coverlayer):
        idx_zone = [idx for idx, name in enumerate(univar[0]) if name == "zone"][0]
        zone_ids = list(dict.fromkeys([int(zoneid[idx_zone]) for zoneid in univar[1:]]))
        if temp_type == "absolute":
            if not bool(idx_end):
                date_points = [
                    datetime.strptime(x[idx_start], "%Y-%m-%d %H:%M:%S")
                    for x in univar[1:]
                    if int(x[idx_zone]) == zone_ids[0]
                ]
            else:
                date_start = [
                    int(
                        datetime.strptime(x[idx_start], "%Y-%m-%d %H:%M:%S").strftime(
                            "%s"
                        )
                    )
                    for x in univar[1:]
                    if int(x[idx_zone]) == zone_ids[0]
                ]
                date_end = [
                    int(
                        datetime.strptime(x[idx_end], "%Y-%m-%d %H:%M:%S").strftime(
                            "%s"
                        )
                    )
                    for x in univar[1:]
                    if int(x[idx_zone]) == zone_ids[0]
                ]
                date_points = [
                    datetime.fromtimestamp(s + (e - s) / 2).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    for s, e in zip(date_start, date_end)
                ]
                date_points = [
                    datetime.strptime(dp, "%Y-%m-%d %H:%M:%S") for dp in date_points
                ]
        else:
            if not bool(idx_end):
                date_points = [
                    int(x[idx_start])
                    for x in univar[1:]
                    if int(x[idx_zone]) == zone_ids[0]
                ]
            else:
                date_start = [
                    int(x[idx_start])
                    for x in univar[1:]
                    if int(x[idx_zone]) == zone_ids[0]
                ]
                date_end = [
                    int(x[idx_end])
                    for x in univar[1:]
                    if int(x[idx_zone]) == zone_ids[0]
                ]
                date_points = [s + (e - s) / 2 for s, e in zip(date_start, date_end)]
        for i, _ in enumerate(zone_ids):
            m = [
                float(x[idx_mean])
                for x in univar[1:]
                if int(x[idx_zone]) == zone_ids[i]
            ]
            mean_vals.append(m)
            if error:
                s = [
                    float(x[idx_sd])
                    for x in univar[1:]
                    if int(x[idx_zone]) == zone_ids[i]
                ]
                if error == "se":
                    d = [
                        float(x[idx_n])
                        for x in univar[1:]
                        if int(x[idx_zone]) == zone_ids[i]
                    ]
                    s = [si / sqrt(di) if di != 0 else 0 for si, di in zip(s, d)]
                upper_limit_vals.append([m + s * n for m, s in zip(m, s)])
                lower_limit_vals.append([m - s * n for m, s in zip(m, s)])
    else:
        if temp_type == "absolute":
            if not bool(idx_end):
                date_points = [
                    datetime.strptime(x[idx_start], "%Y-%m-%d %H:%M:%S")
                    for x in univar[1:]
                ]
                date_points = [
                    datetime.strptime(dp, "%Y-%m-%d %H:%M:%S") for dp in date_points
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
                date_points = [
                    datetime.strptime(dp, "%Y-%m-%d %H:%M:%S") for dp in date_points
                ]
        else:
            if not bool(idx_end):
                date_points = [int(x[idx_start]) for x in univar[1:]]
            else:
                date_start = [int(x[idx_start]) for x in univar[1:]]
                date_end = [int(x[idx_end]) for x in univar[1:]]
                date_points = [s + (e - s) / 2 for s, e in zip(date_start, date_end)]
        m = [float(x[idx_mean]) for x in univar[1:]]
        mean_vals.append(m)
        if error:
            s = [float(x[idx_sd]) for x in univar[1:]]
            if error == "se":
                d = [float(x[idx_n]) for x in univar[1:]]
                s = [si / sqrt(di) for si, di in zip(s, d)]
            upper_limit_vals.append([m + s * n for m, s in zip(m, s)])
            lower_limit_vals.append([m - s * n for m, s in zip(m, s)])
        zone_ids = ""

    # Return values
    return [date_points, mean_vals, upper_limit_vals, lower_limit_vals, zone_ids]


def get_raster_colors(coverlayer, cats_ids):
    """Get colors of cover layer

    :param str coverlayer: name of zonal raster layer
    :param list cats_ids: list with categories from the zonal map

    :return list: list with colors of the zones in the zonal map
    """
    cz = gs.read_command("r.colors.out", map=coverlayer).split("\n")
    cz = [_f for _f in cz if _f]
    cz = [x.split(" ") for x in cz]
    cz = [get_valid_color(x[1]) for x in cz if x[0] in str(cats_ids)]
    return cz


def main(options, flags):
    """
    Draws the boxplot of raster values. Optionally, this is done per
    category of a zonal raster layer
    """

    # lazy import matplotlib
    lazy_import_py_modules()

    # Get strds type
    t_info = gs.parse_command("t.info", flags="g", input=options["input"])
    temp_type = t_info["temporal_type"]

    # Get stats
    if options["n"]:
        n = float(options["n"])
    else:
        n = 1
    x, y_mean, y_ul, y_ll, zone_ids = line_stats(
        strds=options["input"],
        coverlayer=options["zones"],
        error=options["error"],
        n=n,
        threads=int(options["nprocs"]),
        temp_type=temp_type,
        where=options["where"],
    )

    # Get IDs and colors of the categories of the zonal layer
    if options["zones"]:
        check_integer(options["zones"])
        cats_ids, cats_names = get_categories(
            coverlayer=options["zones"], zone_cats=zone_ids
        )
        line_colors = get_raster_colors(options["zones"], cats_ids)
    else:
        line_colors = get_valid_color(options["line_color"])
        cats_ids = ""

    # Output settings
    output = options["output"]
    if bool(options["dpi"]):
        dpi = float(options["dpi"])
    else:
        dpi = 300

    # Plot format settings
    plt.rcParams["font.size"] = int(options["font_size"])
    grid = flags["g"]
    if bool(options["line_width"]):
        line_width = float(options["line_width"])
    if options["plot_dimensions"]:
        dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    else:
        dimensions = [6, 4]

    # Plot the figure
    fig, ax = plt.subplots(figsize=dimensions)
    if options["zones"]:
        if options["error"]:
            for i, _ in enumerate(cats_ids):
                ax.fill_between(
                    x,
                    y_ll[i],
                    y_ul[i],
                    color=line_colors[i],
                    alpha=float(options["alpha"]),
                )
        for i, _ in enumerate(cats_ids):
            ax.plot(x, y_mean[i], label=cats_names[i], color=line_colors[i])
    else:
        ax.plot(x, y_mean[0], color=line_colors)
        if options["error"]:
            ax.fill_between(
                x, y_ll[0], y_ul[0], color=line_colors, alpha=float(options["alpha"])
            )

    # Set granularity and format of date on x axis
    if temp_type == "absolute":
        if not options["date_interval"]:
            locator = mdates.AutoDateLocator(interval_multiples=True)
        else:
            dt = options["date_interval"].capitalize()
            date_locator = f"mdates.{dt}Locator()"
            locator = eval(date_locator)
        ax.xaxis.set_major_locator(locator)
        if options["date_format"]:
            formatter = mdates.DateFormatter(options["date_format"])
            ax.xaxis.set_major_formatter(formatter)
        else:
            formatter = mdates.ConciseDateFormatter(locator)
            ax.xaxis.set_major_formatter(formatter)

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
        plt.ylim([minlim, maxlim])

    # Set grid (optional)
    ax.xaxis.grid(bool(grid))

    # Add legend
    if flags["l"] and options["zones"]:
        ax.legend()

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
