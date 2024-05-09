#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.rast.boxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws the boxplot of the rasters of a space-time
#               raster dataset.
#
# COPYRIGHT:    (c) 2022 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws the boxplot of the raster maps of a space-time raster dataset
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

# %flag
# % key: o
# % label: Include outliers
# % description: Draw boxplot(s) with outliers
# % guisection: Statistics
# %end

# %flag
# % key: n
# % label: Draw notch
# % description: Draw boxplot(s) with notch
# % guisection: Statistics
# %end

# %option
# % key: range
# % type: double
# % label: Range (value > 0)
# % description: This determines how far the plot whiskers extend out from the box. If range is positive, the whiskers extend to the most extreme data point which is no more than range times the interquartile range from the box. A value of zero causes the whiskers to extend to the data extremes.
# % required: no
# % answer: 1.5
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

# %flag
# % key: h
# % label: Horizontal boxplot(s)
# % description: Draw the boxplot horizontal
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
# % key: fontsize
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
# % key: bx_width
# % type: double
# % label: Boxplot width
# % description: The width of the boxplots
# % required: no
# % guisection: Boxplot format
# %end

# %options G_OPT_CN
# % key: bx_color
# % type: string
# % label: Boxplot color
# % description: Color of the boxplots. See manual page for color notation options.
# % required: no
# % answer: white
# % guisection: Boxplot format
# %end

# %option
# % key: bx_lw
# % type: double
# % label: boxplot linewidth
# % description: The linewidth of the boxplots
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
# % key: whisker_linewidth
# % type: double
# % label: Whisker and cap linewidth
# % description: The linewidth of the whiskers and caps
# % required: no
# % guisection: Boxplot format
# % answer: 1
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


import atexit
import sys
import uuid
from subprocess import PIPE

from dateutil import parser

import matplotlib.dates as mdates

import grass.script as gs
from grass.pygrass.modules import Module


clean_maps = []


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


def create_unique_name(name):
    """Generate a temporary name which contains prefix
    Store the name in the global list.

    :param str name: prefix to be used for unique string

    :return str: Unique string with user defined prefix
    """
    unique_string = f"{name}{uuid.uuid4().hex}"
    return unique_string


def create_temporary_name(prefix):
    """Create temporary file name and add this to clean_maps

    :param str name: prefix to be used for unique string

    :return str: Unique string with user defined prefix
    """
    tmpf = create_unique_name(prefix)
    clean_maps.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps specified in the global list"""
    maps = reversed(clean_maps)
    mapset = gs.gisenv()["MAPSET"]
    for map_name in maps:
        for element in ("raster", "vector"):
            found = gs.find_file(
                name=map_name,
                element=element,
                mapset=mapset,
            )
            if found["file"]:
                Module(
                    "g.remove",
                    flags="f",
                    type=element,
                    name=map_name,
                    quiet=True,
                )


def strip_mapset(name, join_char="@"):
    """Strip Mapset name and '@' from map name
    >>> strip_mapset('elevation@PERMANENT')
    elevation

    :param str name: map name
    :param str join_char: Character separating map and mapset name

    :return str: mapname without the mapset name
    """
    return name.split(join_char)[0] if join_char in name else name


def get_rast_name_dates(rasters, col_sep):
    """Create list of names, tic positions, dates and temporal type
    of raster layers in input strds

    :param str rasters: rasters (output of the t.rast.list module)
    :param str col_sep: column separator e.g. "2000_01_tempmean|
                                               2000-01-01 00:00:00|absolute"

    :return tuple: tuple with list of dates, list of raster names,
                         list of tic positions and temporal type of
                         raster layers
    """
    raster_names = []
    raster_dates = []
    temp_types = set()
    tic_positions = []
    for raster in rasters.splitlines():
        raster_name, raster_date, temp_type = raster.split(col_sep)
        raster_names.append(raster_name)
        raster_dates.append(raster_date)
        temp_types.add(temp_type)
        if temp_type == "relative":
            tic_positions.append(int(raster_date))
        else:
            tic_positions.append(
                mdates.date2num(
                    parser.parse(timestr=raster_date),
                )
            )
    return (raster_names, raster_dates, tic_positions, list(temp_types)[0])


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


def get_output_options(option_dpi, option_dimensions, flag_h):
    """Get options for plot (option_dpi, option_dimensions)

    :param str option_dpi: set dpi of plot (if saved as images)
    :param str option_dimensions: set plot dimensions (width, length)
    :param bolean vertical: -h flag to determine if plot needs to be
                            plotted vertical or horizonal

    :return list: list with dpi, list plot dimension, and boolean
                  that sets orientation of boxplots (vertical or
                  horizontal)
    """
    if flag_h:
        vertical = False
    else:
        vertical = True
    if option_dpi:
        dpi = float(option_dpi)
    else:
        dpi = 300
    if option_dimensions:
        dimensions = [float(x) for x in option_dimensions.split(",")]
    else:
        if vertical:
            dimensions = [6, 4]
        else:
            dimensions = [6, 4]
    return [dpi, dimensions, vertical]


def get_bx_width(option_bxp_width, temp_type, strds):
    """Compute the width of the boxpltos

    :param str option_bxp_width: user defined boxplot width
    :param str temp_type: temporal type of stdrs (absolute or relative)
    :param str strds: name of the input strds

    :return list: list with bxp_width, temp_lngt and temp_unit
    """
    if option_bxp_width:
        bxp_width = float(option_bxp_width)
    else:
        bxp_width = 0.7
    if temp_type == "relative":
        bxp_width = 0.7
    else:
        strds_info = Module(
            "t.info", flags="g", input=strds, stdout_=PIPE
        ).outputs.stdout
        temp_unit = (
            strds_info.split("\n")[10].split("=")[1].split(" ")[1].replace("'", "")
        )
        temp_lngt = int(
            strds_info.split("\n")[10].split("=")[1].split(" ")[0].replace("'", "")
        )
        temp_options = {
            "years": 365 * bxp_width * temp_lngt,
            "months": 30 * bxp_width * temp_lngt,
            "days": bxp_width * temp_lngt,
            "hours": 1 / 24 * bxp_width * temp_lngt,
            "minutes": 1 / 1440 * bxp_width * temp_lngt,
            "seconds": 1 / 86400 * bxp_width * temp_lngt,
            "year": 365 * bxp_width,
            "month": 30 * bxp_width,
            "day": bxp_width,
            "hour": 1 / 24 * bxp_width,
            "minute": 1 / 1440 * bxp_width,
            "second": 1 / 86400 * bxp_width,
        }
        bxp_width = temp_options[temp_unit]
    return [bxp_width, temp_lngt, temp_unit]


def bxp_stats(rastername, whisker_range):
    """Compute boxplot statistics

    :param str rastername: name of input raster
    :param float whisker_range: number representing the whisker range

    :return list: list with minimum value, 1st, 2nd and 3rd
                  quantiles and maximum value of the input raster
    """
    quantile_rules = Module(
        "r.quantile",
        flags="r",
        input=rastername,
        percentiles=[25, 50, 75],
        stdout_=PIPE,
    ).outputs.stdout
    quantile_rules = quantile_rules.replace("\r", "").split("\n")
    quantile_rules = [_f for _f in quantile_rules if _f]
    quantiles = [x.split(":") for x in quantile_rules]
    min_value = float(quantiles[0][0])
    quant1 = float(quantiles[0][1])
    quant2 = float(quantiles[1][1])
    quant3 = float(quantiles[2][1])
    max_value = float(quantiles[3][1])

    # Compute iqr and whisker limits
    iqr = whisker_range * (quant3 - quant1)
    lower_bound = quant1 - iqr
    if lower_bound > min_value:
        lower_whisker = lower_bound
    else:
        lower_whisker = min_value
    upper_bound = quant3 + iqr
    if upper_bound < max_value:
        upper_whisker = upper_bound
    else:
        upper_whisker = max_value

    # Return values
    return [
        min_value,
        quant1,
        quant2,
        quant3,
        max_value,
        iqr,
        lower_whisker,
        upper_whisker,
    ]


def compute_notch(rastername, quant2, iqr):
    """Compute notches of boxplots

    :param str rastername: name of input raster
    :param float quant2: 2nd quantile
    :param float iqr: interquartile range

    :return list: list with lower and upper notch value of input raster
    """
    univar = Module(
        "r.univar", flags=["g", "t"], map=rastername, stdout_=PIPE
    ).outputs.stdout
    n_values = int(univar.replace("\r", "").split("\n")[1].split("|")[0])
    lower_notch = quant2 - 1.57 * (iqr / n_values**0.5)
    upper_notch = quant2 + 1.57 * (iqr / n_values**0.5)
    return [lower_notch, upper_notch]


def compute_outliers(rastername, min_value, max_value, lower_whisker, upper_whisker):
    """Compute notches of boxplots

    :param float min_value: minimum raster raster 'rastername'
    :param float max_value: maximum raster raster 'rastername'
    :param float lower_whisker: lower whisker value 'rastername'
    :param float upper_whisker: upper whisker value 'rastername'

    :return list: list with outlier values for input raster
    """
    # Define recode rules to extract outliers
    lower_outliers = f"{min_value}:{lower_whisker}:1"
    upper_outliers = f"{upper_whisker}:{max_value}:1"
    if min_value < lower_whisker and max_value > upper_whisker:
        recode_rules = "{}\n{}".format(lower_outliers, upper_outliers)
    elif min_value < lower_whisker:
        recode_rules = lower_outliers
    elif max_value > upper_whisker:
        recode_rules = upper_outliers
    else:
        recode_rules = False
    if bool(recode_rules):
        colname = "tmpcolname"
        tmprast = create_temporary_name("tmp01")
        Module(
            "r.recode",
            input=rastername,
            output=tmprast,
            rules="-",
            stdin_=recode_rules,
        )
        vect_name = create_temporary_name("tmpv")
        rast_name = create_temporary_name("tmpr")
        Module(
            "r.mapcalc",
            expression="{} = {}*{}".format(rast_name, tmprast, rastername),
        )
        Module(
            "r.to.vect",
            input=rast_name,
            output=vect_name,
            type="point",
            column=colname,
        )
        fliers = Module(
            "db.select", sql=f"select {colname} from {vect_name}", stdout_=PIPE
        ).outputs.stdout
        fliers = fliers.split("\n")[1:-1]
        fliers = [float(x) for x in fliers]
        remove_names = [tmprast, rast_name, vect_name]
        Module(
            "g.remove",
            flags="f",
            name=remove_names,
            type=["raster", "vector"],
            quiet=True,
        )
    else:
        fliers = []
        gs.message("\n--> There are no outliers")
    return fliers


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

    # Plot format options
    plt.rcParams["font.size"] = int(options["fontsize"])
    grid = flags["g"]

    # Get range (if defined)
    whisker_range = float(options["range"])
    range_min_val = 0
    if whisker_range <= range_min_val:
        gs.fatal(
            _(
                "The range value need to be larger than {min_val}".format(
                    min_val=range_min_val,
                )
            )
        )

    # Line width boxplot and whiskers
    bxp_linewidth = float(options["bx_lw"])
    whisker_linewidth = float(options["whisker_linewidth"])

    # Get flier size, marker and color
    flier_size = int(options["flier_size"])
    flier_marker = options["flier_marker"]
    flier_color = get_valid_color(color=options["flier_color"])

    # Boxplot fill color
    bxcolor = get_valid_color(options["bx_color"])

    # Output options
    output = options["output"]
    dpi, dimensions, vertical = get_output_options(
        options["dpi"], options["plot_dimensions"], flags["h"]
    )

    # Get names, dates, tic position and temporal type of raster layers
    rast_names, rast_dates, tic_positions, temp_type = gs.parse_command(
        "t.rast.list",
        flags="u",
        input=options["input"],
        columns=["name", "start_time", "temporal_type"],
        parse=(get_rast_name_dates, {"col_sep": "|"}),
    )

    # Determine boxplot width (based on date type and granuality)
    bxp_width, temp_lngt, temp_unit = get_bx_width(
        options["bx_width"],
        temp_type,
        options["input"],
    )

    # Create the stats and define the boxes
    boxes = []
    for _, rastername in enumerate(rast_names):

        # Compute boxplot stats
        (
            min_value,
            quant1,
            quant2,
            quant3,
            max_value,
            iqr,
            lower_whisker,
            upper_whisker,
        ) = bxp_stats(rastername, whisker_range)

        # Compute notch limits
        if flags["n"]:
            lower_notch, upper_notch = compute_notch(rastername, quant2, iqr)
        else:
            lower_notch = upper_notch = ""

        # Compute outliers
        if flags["o"]:
            fliers = compute_outliers(
                rastername, min_value, max_value, lower_whisker, upper_whisker
            )
        else:
            fliers = []

        # Create box for raster
        dict_i = {
            "whislo": lower_whisker,
            "q1": quant1,
            "med": quant2,
            "q3": quant3,
            "whishi": upper_whisker,
            "fliers": fliers,
            "cilo": lower_notch,
            "cihi": upper_notch,
        }
        boxes.append(dict_i)

    # Plot the figure
    _, ax = plt.subplots(figsize=dimensions)
    boxprops = dict(linewidth=bxp_linewidth)
    whiskerprops = dict(linewidth=whisker_linewidth)
    capprops = dict(linewidth=whisker_linewidth)
    median_color = get_valid_color(options["median_color"])
    medianprops = dict(linewidth=float(options["median_lw"]), color=median_color)
    bxplot = ax.bxp(
        boxes,
        positions=tic_positions,
        showfliers=True,
        widths=bxp_width,
        vert=vertical,
        boxprops=boxprops,
        whiskerprops=whiskerprops,
        medianprops=medianprops,
        capprops=capprops,
        shownotches=bool(flags["n"]),
        patch_artist=True,
        flierprops={
            "marker": flier_marker,
            "markersize": flier_size,
            "markerfacecolor": flier_color,
            "markeredgecolor": flier_color,
        },
    )

    # Set granuality and format of date on x (or y) axis
    if flags["d"]:
        locator = mdates.AutoDateLocator(interval_multiples=True)
        formatter = mdates.ConciseDateFormatter(locator)
        if vertical:
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
        else:
            ax.yaxis.set_major_locator(locator)
            ax.yaxis.set_major_formatter(formatter)
    else:
        ax = set_axis(
            ax, options["date_format"], temp_unit, vertical, rast_dates, temp_lngt
        )

    # Set color boxplots
    bxcolor = [bxcolor for _i in range(len(rast_names))]
    for patch, color in zip(bxplot["boxes"], bxcolor):
        patch.set_facecolor(color)

    # Label orientation
    if bool(options["rotate_labels"]) and vertical:
        rotate_labels = float(options["rotate_labels"])
        if abs(rotate_labels) <= 10 or abs(rotate_labels) >= 80:
            plt.xticks(rotation=rotate_labels)
        elif rotate_labels < 0:
            plt.xticks(rotation=rotate_labels, ha="left", rotation_mode="anchor")
        else:
            plt.xticks(rotation=rotate_labels, ha="right", rotation_mode="anchor")
    elif bool(options["rotate_labels"]) and not vertical:
        rotate_labels = float(options["rotate_labels"])
        if abs(rotate_labels) <= 10 or abs(rotate_labels) >= 80:
            plt.yticks(rotation=rotate_labels)
        else:
            plt.yticks(rotation=rotate_labels, ha="right", rotation_mode="anchor")
    elif vertical:
        plt.xticks(rotation=45, ha="right", rotation_mode="anchor")

    # Set limits value axis
    if bool(options["axis_limits"]):
        minlim, maxlim = map(float, options["axis_limits"].split(","))
        if bool(vertical):
            plt.ylim([minlim, maxlim])
        else:
            plt.xlim([minlim, maxlim])

    # Set grid (optional)
    if vertical:
        ax.yaxis.grid(bool(grid))
    else:
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
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
