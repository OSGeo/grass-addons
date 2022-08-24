#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.series.boxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws the boxplot of the rastrers of a space-time
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
# % description: Default font size
# % guisection: Plot format
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
# % key: boxplot_width
# % type: double
# % label: Boxplot width
# % description: The width of the boxplots
# % required: no
# % guisection: Boxplot format
# %end

# %options G_OPT_CN
# % key: bxcolor
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


import sys
import atexit
import uuid
from subprocess import PIPE
from dateutil import parser
import matplotlib.dates as mdates
import grass.script as gs
from grass.pygrass.modules import Module


clean_layers = []


def create_unique_name(name):
    """Generate a temporary name which contains prefix
    Store the name in the global list.
    """
    return name + str(uuid.uuid4().hex)


def create_temporary_name(prefix):
    """Create temporary file name"""
    tmpf = create_unique_name(prefix)
    clean_layers.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(clean_layers))
    for layername in cleanrast:
        ffile = gs.find_file(
            name=layername, element="cell", mapset=gs.gisenv()["MAPSET"]
        )
        if ffile["file"]:
            Module(
                "g.remove",
                flags="f",
                type="raster",
                name=layername,
                quiet=True,
            )
        vfile = gs.find_file(
            element="vector", name=layername, mapset=gs.gisenv()["MAPSET"]
        )
        if vfile["file"]:
            Module(
                "g.remove",
                flags="f",
                type="vector",
                name=layername,
                quiet=True,
            )


def strip_mapset(name):
    """Strip Mapset name and '@' from map name
    >>> strip_mapset('elevation@PERMANENT')
    elevation
    """
    if "@" in name:
        return name.split("@")[0]
    return name


def main(options, flags):
    """
    Draws the boxplot of raster values. Optionally, this is done per category
    of a zonal raster layer
    """

    # lazy import matplotlib
    try:
        import matplotlib

        matplotlib.use("WXAgg")
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("matplotlib is not installed"))

    # Plot format options
    fontsize = options["fontsize"]
    if fontsize:
        int(fontsize)
        plt.rcParams["font.size"] = fontsize
    else:
        fontsize = 10
    flag_h = flags["h"]
    if flag_h:
        vertical = False
    else:
        vertical = True
    if options["rotate_labels"]:
        rotate_label = float(options["rotate_labels"])
    grid = flags["g"]

    # Get boxplot format options
    whisker_range = options["range"]
    if whisker_range:
        whisker_range = float(whisker_range)
    else:
        whisker_range = 1.5
    if whisker_range <= 0:
        gs.fatal("The range value need to be larger than 0")
    if not options["flier_size"]:
        flier_size = 2
    else:
        flier_size = int(options["flier_size"])
    if not options["flier_marker"]:
        flier_marker = "o"
    else:
        flier_marker = options["flier_marker"]
    flier_color = options["flier_color"]
    if not flier_color:
        flier_color = "black"
    elif ":" in flier_color:
        flier_color = [int(_x) / 255 for _x in options["flier_color"].split(":")]
    if not matplotlib.colors.is_color_like(flier_color):
        gs.fatal(_("{} is not a valid color".format(options["flier_color"])))

    # Statistics options
    outliers = flags["o"]
    notch = flags["n"]

    # Output options
    output = options["output"]
    set_dpi = options["dpi"]
    if set_dpi:
        dpi = float(set_dpi)
    else:
        dpi = 300
    dimensions = options["plot_dimensions"]
    if dimensions:
        dimensions = [float(x) for x in dimensions.split(",")]
    else:
        if vertical:
            dimensions = [6, 6]
        else:
            dimensions = [8, 4]

    # Get names and dates of raster layers
    strds = options["input"]
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

    # Determine boxplot width (based on date type and granuality)
    if options["boxplot_width"]:
        bxp_width = float(options["boxplot_width"])
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
    print(temp_lngt)
    print(temp_unit)

    # Set boxplot colors
    set_bxcolor = options["bxcolor"]
    if set_bxcolor:
        if set_bxcolor[0] == "#":
            bxcolor = set_bxcolor[1:]
            if len(bxcolor) == 3:
                bxcolor = "".join(char + char for char in bxcolor)
                bxcolor = f"#{bxcolor}"
            else:
                bxcolor = set_bxcolor
        elif len(set_bxcolor.split(":")) >= 3 and len(set_bxcolor.split(":")) <= 4:
            bxcolor = set_bxcolor.split(":")
            bxcolor = [float(_x) / 255 for _x in bxcolor]
        else:
            bxcolor = set_bxcolor.replace(" ", "")
        if matplotlib.colors.is_color_like(bxcolor):
            bxcolor = matplotlib.colors.to_rgba(bxcolor)
        else:
            gs.warning(
                _("color definition cannot be interpreted as a color. See manual page.")
            )
        brightness = bxcolor[0] * 0.299 + bxcolor[1] * 0.587 + bxcolor[2] * 0.114
        if brightness > 149 / 255:
            mcolor = [0, 0, 0, 0.7]
        else:
            mcolor = [1, 1, 1, 0.7]
        bxcolor = [bxcolor for _i in range(len(rast_names))]
        mcolor = [mcolor for _i in range(len(rast_names))]

    # Create the stats and define the boxes
    boxes = []
    for rasterid, rastername in enumerate(rast_names):
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

        # Extract boxplot stats
        min_value = float(quantiles[0][0])
        quantile_1 = float(quantiles[0][1])
        quantile_2 = float(quantiles[1][1])
        quantile_3 = float(quantiles[2][1])
        max_value = float(quantiles[3][1])

        # Compute iqr and whisker limits
        iqr = whisker_range * (quantile_3 - quantile_1)
        lower_bound = quantile_1 - iqr
        if lower_bound > min_value:
            lower_whisker = lower_bound
        else:
            lower_whisker = min_value
        upper_bound = quantile_3 + iqr
        if upper_bound < max_value:
            upper_whisker = upper_bound
        else:
            upper_whisker = max_value

        # Compute notch limits
        if notch:
            univar = Module(
                "r.univar", flags=["g", "t"], map=rastername, stdout_=PIPE
            ).outputs.stdout
            n_values = int(univar.replace("\r", "").split("\n")[1].split("|")[0])
            lower_notch = quantile_2 - 1.57 * (iqr / n_values**2)
            upper_notch = quantile_2 + 1.57 * (iqr / n_values**2)
        else:
            lower_notch = ""
            upper_notch = ""

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

        # If outliers are asked for, extract their values
        if outliers and bool(recode_rules):
            colname = f"col{rasterid}"
            tmprast = create_temporary_name("tmp01")
            Module(
                "r.recode",
                input=rastername,
                output=tmprast,
                rules="-",
                stdin_=recode_rules,
            )
            vect_name = create_temporary_name("tmp")
            rast_name = create_temporary_name("tmp")
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
        elif outliers and not recode_rules:
            fliers = []
            gs.message("\n--> There are no outliers")
        else:
            fliers = []

        # Create box for raster
        dict_i = {
            "whislo": lower_whisker,
            "q1": quantile_1,
            "med": quantile_2,
            "q3": quantile_3,
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
        shownotches=notch,
        patch_artist=set_bxcolor,
        flierprops={
            "marker": flier_marker,
            "markersize": flier_size,
            "markerfacecolor": flier_color,
            "markeredgecolor": flier_color,
        },
    )
    if "year" in temp_unit:
        # locator = mdates.YearLocator()
        if options["date_format"]:
            date_fmt = mdates.DateFormatter(options["date_format"])
        else:
            date_fmt = mdates.DateFormatter("%Y")
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
        else:
            ax.yaxis.set_major_formatter(date_fmt)
    if "month" in temp_unit:
        # locator = mdates.MonthLocator()
        if options["date_format"]:
            date_fmt = mdates.DateFormatter(options["date_format"])
        else:
            date_fmt = mdates.DateFormatter("%Y-%m")
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
        else:
            ax.yaxis.set_major_formatter(date_fmt)
    if "day" in temp_unit:
        # locator = mdates.DayLocator()
        if options["date_format"]:
            date_fmt = mdates.DateFormatter(options["date_format"])
        else:
            date_fmt = mdates.DateFormatter("%Y-%m-%d")
        if vertical:
            ax.xaxis.set_major_formatter(date_fmt)
        else:
            ax.yaxis.set_major_formatter(date_fmt)
    if "hour" in temp_unit:
        # locator = mdates.HourLocator()
        if options["date_format"]:
            date_fmt = mdates.DateFormatter(options["date_format"])
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
        # locator = mdates.MinuteLocator()
        if options["date_format"]:
            date_fmt = mdates.DateFormatter(options["date_format"])
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
        # locator = mdates.SecondLocator()
        if options["date_format"]:
            date_fmt = mdates.DateFormatter(options["date_format"])
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

    if set_bxcolor:
        for patch, color in zip(bxplot["boxes"], bxcolor):
            patch.set_facecolor(color)
        for median, mediancolor in zip(bxplot["medians"], mcolor):
            median.set_color(mediancolor)
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
