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
# % description: Draws the boxplot of the rastrers of a space-time raster dataset
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
# % options: 0-365
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
# % description: Font size labe
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
# % guisection: Boxplot format
# %end

# %option
# % key: flier_marker
# % type: string
# % label: Flier marker
# % description: Set flier marker (see https://matplotlib.org/stable/api/markers_api.html for options)
# % required: no
# % guisection: Boxplot format
# %end

# %option
# % key: flier_size
# % type: string
# % label: Flier size
# % description: Set the flier size
# % required: no
# % guisection: Boxplot format
# %end

# %option G_OPT_C
# % key: flier_color
# % label: Flier color
# % description: Set the flier color
# % required: no
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


def get_rast_name_dates(option_input):
    """Create list of names, tic positions, dates and temporal type
       of raster layers in input strds

    :param str option_input: Name of the input strds

    :return list: list with list of dates, list of raster names,
                  list of tic positions and temporal type of
                  raster layers
    """
    # Get names, dates and types of raster layers
    strds = option_input
    strds_rasters = Module(
        "t.rast.list",
        flags="u",
        input=strds,
        columns=["name", "start_time", "temporal_type"],
        stdout_=PIPE,
    ).outputs.stdout
    strds_rasters = strds_rasters.split("\n")
    strds_rasters = [_f for _f in strds_rasters if _f]
    rast_names = [z.split("|")[0] for z in strds_rasters]
    rast_dates = [z.split("|")[1] for z in strds_rasters]

    temp_type = [z.split("|")[2] for z in strds_rasters]
    if not temp_type.count(temp_type[0]) == len(temp_type):
        gs.fatal(
            _("All raster layers in the strd need to be of the same temporal type")
        )
    else:
        temp_type = temp_type[0]
    if temp_type == "relative":
        tic_positions = [int(z) for z in rast_dates]
    else:
        rast_dates = [parser.parse(timestr=datestr) for datestr in rast_dates]
        tic_positions = mdates.date2num(rast_dates)
    return [rast_names, rast_dates, tic_positions, temp_type]


def get_flier_options(flier_size, flier_marker, flier_color):
    """Set the flier size, marker and color

    :param str flier_size: size of flier
    :param str flier_marker: flier marker
    :param str flier_color: flier color

    :return list: list with flier size, marker and color
    """
    # Set flier options
    if not flier_size:
        flier_size = 2
    else:
        flier_size = int(flier_size)
    if not flier_marker:
        flier_marker = "o"
    if not flier_color:
        flier_color = "black"
    elif ":" in flier_color:
        flier_color = [int(_x) / 255 for _x in flier_color.split(":")]
    if not matplotlib.colors.is_color_like(flier_color):
        gs.fatal(_("{} is not a valid color".format(flier_color)))
    return [flier_size, flier_marker, flier_color]


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
            dimensions = [6, 6]
        else:
            dimensions = [8, 4]
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


def get_bxp_color(bxp_color, number_layers):
    """Get the user-defined colors for the boxplots, and compute
    the colors of the median line.

    :param str bxp_color: user defined boxplot color
    :param str rast_layer: name of input raster layer

    :return list: list of boxplot color (bxcolor and median line(mxcolor)
    """
    if bxp_color == "none":
        bxp_fill = False
        bxcolor = ""
        mcolor = ""
    elif bxp_color:
        if bxp_color[0] == "#":
            bxcolor = bxp_color[1:]
            if len(bxcolor) == 3:
                bxcolor = "".join(char + char for char in bxcolor)
                bxcolor = f"#{bxcolor}"
            else:
                bxcolor = bxp_color
        elif len(bxp_color.split(":")) >= 3 and len(bxp_color.split(":")) <= 4:
            bxcolor = bxp_color.split(":")
            bxcolor = [float(_x) / 255 for _x in bxcolor]
        else:
            bxcolor = bxp_color.replace(" ", "")
        if matplotlib.colors.is_color_like(bxcolor):
            bxcolor = matplotlib.colors.to_rgba(bxcolor)
        else:
            gs.warning(
                _("color definition cannot be interpreted as a color. See manual page.")
            )
        if bxp_color == "none":
            mcolor = ""
        else:
            brightness = bxcolor[0] * 0.299 + bxcolor[1] * 0.587 + bxcolor[2] * 0.114
            if brightness > 149 / 255:
                mcolor = [0, 0, 0, 0.7]
            else:
                mcolor = [1, 1, 1, 0.7]
        bxcolor = [bxcolor for _i in range(number_layers)]
        mcolor = [mcolor for _i in range(number_layers)]
        bxp_fill = True
    else:
        bxp_fill = False
    return [bxcolor, mcolor, bxp_fill]


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
    lower_notch = quant2 - 1.57 * (iqr / n_values**2)
    upper_notch = quant2 + 1.57 * (iqr / n_values**2)
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
        start_time = mdates.date2num(rast_dates[0]) - 1 / 48 * temp_lngt
        end_time = mdates.date2num(rast_dates[-1]) + 1 / 48 * temp_lngt
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
        start_time = mdates.date2num(rast_dates[0]) - 1 / 2880 * temp_lngt
        end_time = mdates.date2num(rast_dates[-1]) + 1 / 2880 * temp_lngt
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
        start_time = mdates.date2num(rast_dates[0]) - 1 / 172800 * temp_lngt
        end_time = mdates.date2num(rast_dates[-1]) + 1 / 172800 * temp_lngt
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

    global matplotlib
    global plt

    # lazy import matplotlib
    lazy_import_py_modules()

    # Plot format options
    plt.rcParams["font.size"] = int(options["fontsize"])
    if options["rotate_labels"]:
        rotate_label = float(options["rotate_labels"])
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

    # Get flier size, marker and color
    flier_size, flier_marker, flier_color = get_flier_options(
        options["flier_size"], options["flier_marker"], options["flier_color"]
    )

    # Output options
    output = options["output"]
    dpi, dimensions, vertical = get_output_options(
        options["dpi"], options["plot_dimensions"], flags["h"]
    )

    # Get names, dates, tic position and temporal type of raster layers
    strds = options["input"]
    rast_names, rast_dates, tic_positions, temp_type = get_rast_name_dates(strds)

    # Get boxplot color color median lne
    bxcolor, mcolor, bxp_fill = get_bxp_color(options["bx_color"], len(rast_names))

    # Determine boxplot width (based on date type and granuality)
    bxp_width, temp_lngt, temp_unit = get_bx_width(
        options["bx_width"], temp_type, strds
    )

    # Create the stats and define the boxes
    boxes = []
    for rasterid, rastername in enumerate(rast_names):

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
    bxplot = ax.bxp(
        boxes,
        positions=tic_positions,
        showfliers=True,
        widths=bxp_width,
        vert=vertical,
        shownotches=bool(flags["n"]),
        patch_artist=bxp_fill,
        flierprops={
            "marker": flier_marker,
            "markersize": flier_size,
            "markerfacecolor": flier_color,
            "markeredgecolor": flier_color,
        },
    )

    # Set granuality and format of date on x (or y) axis
    ax = set_axis(
        ax, options["date_format"], temp_unit, vertical, rast_dates, temp_lngt
    )

    # Set color median lines
    if bxp_fill:
        for patch, color in zip(bxplot["boxes"], bxcolor):
            patch.set_facecolor(color)
        for median, mediancolor in zip(bxplot["medians"], mcolor):
            median.set_color(mediancolor)

    # Label orientation
    if options["rotate_labels"] and vertical:
        plt.xticks(rotation=rotate_label)
    if options["rotate_labels"] and not vertical:
        plt.yticks(rotation=rotate_label)
    if grid:
        if vertical:
            ax.yaxis.grid(True)
        else:
            ax.xaxis.grid(True)
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
