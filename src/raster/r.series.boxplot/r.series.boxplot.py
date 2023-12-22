#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.series.boxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws boxplots of a series of input rasters.
#
# COPYRIGHT:    (c) 2022 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws the boxplot of raster values of a series of input rasters.
# % keyword: display
# % keyword: raster
# % keyword: plot
# % keyword: boxplot
# % keyword: statistics
# %end

# %option G_OPT_R_MAPS
# % description: input raster
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % key_desc: file name
# % label: Name of output image file
# % required: no
# % guisection: Output
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
# % key: dpi
# % type: integer
# % label: DPI
# % description: Set the resolution of plot
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
# % label: Draw the notch
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
# % key: text_labels
# % type: string
# % label: Boxplot text labels
# % description: Give labels of the boxplots (comma separated). If you leave this empty, the raster layer names will be used as labels.
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
# % label: Rotate labels (degrees)
# % description: Rotate labels (degrees)
# % guisection: Plot format
# %end

# %option
# % key: boxplot_width
# % type: double
# % label: Set boxplot width
# % description: The width of the boxplots (0,1])
# % required: no
# % guisection: Plot format
# %end

# %flag
# % key: g
# % label: grid lines
# % description: add grid lines
# % guisection: Plot format
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
# % key: fontsize
# % type: integer
# % label: Font size
# % description: Default font size
# % guisection: Boxplot format
# % required: no
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
# % description: Set flier size
# % required: no
# % guisection: Boxplot format
# %end

# %option G_OPT_C
# % key: flier_color
# % label: Flier color
# % description: Set flier color
# % required: no
# % guisection: Boxplot format
# %end

import sys
import atexit
import uuid
from subprocess import PIPE
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

    # input options
    rasters = options["map"].split(",")
    output = options["output"]
    outliers = flags["o"]
    if bool(options["rotate_labels"]):
        rotate_label = float(options["rotate_labels"])
    notch = flags["n"]
    grid = flags["g"]
    if options["fontsize"]:
        plt.rcParams["font.size"] = int(options["fontsize"])
    else:
        plt.rcParams["font.size"] = 10
    if options["range"]:
        whisker_range = float(options["range"])
    else:
        whisker_range = 1.5
    if whisker_range <= 0:
        gs.fatal("The range value need to be larger than 0")
    if options["dpi"]:
        dpi = float(options["dpi"])
    else:
        dpi = 300
    if flags["h"]:
        vertical = False
    else:
        vertical = True
    if options["plot_dimensions"]:
        dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    else:
        if vertical:
            dimensions = [6, 6]
        else:
            dimensions = [8, 4]
    bxp_width = options["boxplot_width"]
    if bool(bxp_width):
        bxp_width = float(bxp_width)
        if bxp_width > 1 or bxp_width <= 0:
            gs.fatal(_("The boxplot width needs to in the interval (0,1]"))
    else:
        bxp_width = 0.65
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
            gs.fatal(
                _(
                    "color definition cannot be interpreted as a color.  See manual page."
                )
            )
        brightness = bxcolor[0] * 0.299 + bxcolor[1] * 0.587 + bxcolor[2] * 0.114
        if bxcolor == (0.0, 0.0, 0.0, 0.0):
            mcolor = "black"
        elif brightness > 149 / 255:
            mcolor = [0, 0, 0, 0.7]
        else:
            mcolor = [1, 1, 1, 0.7]
        bxcolor = [bxcolor for _i in range(len(rasters))]
        mcolor = [mcolor for _i in range(len(rasters))]
    if not options["flier_size"]:
        flier_size = 2
    else:
        flier_size = int(options["flier_size"])
    if not options["flier_marker"]:
        flier_marker = "o"
    else:
        flier_marker = options["flier_marker"]
    if not options["flier_color"]:
        flier_color = "black"
    elif ":" in options["flier_color"]:
        flier_color = [int(_x) / 255 for _x in options["flier_color"].split(":")]
    else:
        flier_color = options["flier_color"]
    if not matplotlib.colors.is_color_like(flier_color):
        gs.fatal(_("{} is not a valid color".format(options["flier_color"])))
    if bool(options["text_labels"]):
        list_text_labels = options["text_labels"].split(",")
        if len(list_text_labels) != len(rasters):
            gs.fatal(
                _(
                    "The number of labels you provided is not equal to the number of input rasters"
                )
            )
        else:
            labels = list_text_labels
    else:
        labels = [strip_mapset(_x) for _x in rasters]

    # Create the stats and define the boxes
    boxes = []
    for rasterid, rastername in enumerate(rasters):
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
            lower_notch = quantile_2 - 1.57 * (iqr / n_values**0.5)
            upper_notch = quantile_2 + 1.57 * (iqr / n_values**0.5)
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
            colname = strip_mapset(rastername)
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
            "label": labels[rasterid],
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
    if set_bxcolor:
        for patch, color in zip(bxplot["boxes"], bxcolor):
            patch.set_facecolor(color)
        for median, mcolor in zip(bxplot["medians"], mcolor):
            median.set_color(mcolor)

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

    # Set grid
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
