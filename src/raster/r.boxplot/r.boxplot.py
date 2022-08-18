#!/usr/bin/env python

############################################################################
#
# MODULE:       r.boxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws boxplot(s) of raster values of the input raster.
#               Optionally, this can be done per category of a zonal map.
#
# COPYRIGHT:    (c) 2022 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws the boxplot of raster values. Optionally, this is done per category of a zonal raster layer
# % keyword: display
# % keyword: raster
# % keyword: plot
# % keyword: boxplot
# %end

# %option G_OPT_R_MAP
# % key: input
# % description: input raster
# % required: yes
# % label: Input raster
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
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: resolution of plot
# % required: no
# % guisection: Output
# %end

# %option
# % key: map_outliers
# % type: string
# % label: Name of outlier map
# % description: Create a vector point layer of outliers
# % guisection: Outliers
# % required: no
# %end

# %option
# % key: flier_marker
# % type: string
# % label: Flier marker
# % description: flier marker
# % required: no
# % guisection: Outliers
# %end

# %option
# % key: flier_size
# % type: string
# % label: Flier size
# % description: flier size
# % required: no
# % guisection: Outliers
# %end

# %option G_OPT_C
# % key: flier_color
# % label: Flier color
# % description: flier color
# % required: no
# % guisection: Outliers
# %end

# %flag
# % key: o
# % label: Include outliers
# % description: Draw boxplot(s) with outliers
# % guisection: Outliers
# %end

# %rules
# % requires: map_outliers, -o
# %end

# %option
# % key: order
# % type: string
# % label: Sort boxplots
# % description: Sort boxplots based on their median values
# % required: no
# % options: descending,ascending
# % guisection: Plot options
# %end


# %option
# % key: fontsize
# % type: integer
# % label: Font size
# % description: Default font size
# % guisection: Output
# % required: no
# %end

# %flag
# % key: h
# % label: Horizontal boxplot(s)
# % description: Draw the boxplot horizontal
# % guisection: Plot options
# %end

# %flag
# % key: r
# % label: Rotate labels
# % description: rotate labels
# % guisection: Plot options
# %end


# %option
# % key: boxplot_width
# % type: double
# % label: Boxplot width
# % description: The width of the boxplots (0,1])
# % required: no
# % guisection: Plot options
# %end

# %flag
# % key: c
# % label: Color boxplots
# % description: Color boxploxs using the colors of the categories of the zonal raster
# % guisection: Plot options
# %end

# %flag
# % key: s
# % label: Show category numbers
# % description: Show the category numbers of the zonal map
# % guisection: Plot options
# %end

# %option G_OPT_C
# %key: raster_stat_color
# %label: Color of the raster IQR and median
# %description: Color of raster IQR and median
# %required: no
# %answer: grey
# %guisection: Plot options
# %end

# %option
# % key: raster_stat_alpha
# % type: double
# % description: Transparency of the raster IQR band
# % required: no
# %options: 0-1
# %answer: 0.2
# % guisection: Plot options
# %end

# %flag
# % key: n
# % label: Draw notches
# % description: Draw boxplot(s) with notch
# % guisection: Statistics
# %end

# %option
# % key: range
# % type: double
# % label: Range (value > 0)
# % description: this determines how far the plot whiskers extend out from the box. If range is positive, the whiskers extend to the most extreme data point which is no more than range times the interquartile range from the box. A value of zero causes the whiskers to extend to the data extremes.
# % required: no
# % answer: 1.5
# % guisection: Statistics
# %end

# %option
# % key: raster_statistics
# % type: string
# % description: Plot the raster median and IQR
# % required: no
# % multiple: yes
# % options: median, IQR
# % guisection: Statistics
# %end

# %flag
# % key: g
# % label: Respect region settings
# % description: Use region instead of extent and resolution of zonal map
# %end

# %rules
# % requires: -r, zones
# %end

# %rules
# % requires: -c, zones
# %end

# %rules
# % requires: -s, zones
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


def checkmask():
    """Check if there is a MASK set"""
    ffile = gs.find_file(name="MASK", element="cell", mapset=gs.gisenv()["MAPSET"])
    mask_presence = ffile["name"] == "MASK"
    return mask_presence


def strip_mapset(name):
    """Strip Mapset name and '@' from map name
    >>> strip_mapset('elevation@PERMANENT')
    elevation
    """
    if "@" in name:
        return name.split("@")[0]
    return name


def check_integer(name):
    """Check if map values are integer"""
    input_info = gs.raster_info(name)
    if input_info["datatype"] != "CELL":
        gs.fatal(_("The zonal raster must be of type CELL (integer)"))


def raster_stats(name):
    # Compute statistics
    quantile_rules = Module(
        "r.quantile",
        flags="r",
        input=name,
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

    # Return values
    return min_value, quantile_1, quantile_2, quantile_3, max_value


def bxp_nozones(
    name,
    outliers,
    output,
    dimensions,
    dpi,
    vertical,
    notch,
    rotate_label,
    name_outliers_map,
    whisker_range,
    fontsize,
    bxp_width,
    flier_size,
    flier_marker,
    flier_color,
):
    """Compute the statistics used to create the boxplot,
    and create the boxplot. This function is used in case
    no zonal raster is provided."""

    # Compute statistics
    min_value, quantile_1, quantile_2, quantile_3, max_value = raster_stats(name=name)

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
            "r.univar", flags=["g", "t"], map=name, stdout_=PIPE
        ).outputs.stdout
        n_values = int(univar.replace("\r", "").split("\n")[1].split("|")[0])
        lower_notch = quantile_2 - 1.57 * (iqr / n_values**2)
        upper_notch = quantile_2 + 1.57 * (iqr / n_values**2)
    else:
        lower_notch = ""
        upper_notch = ""

    # Define recode rules to extract outliers
    lower_outlier_bnd = lower_whisker - 0.000000000001
    lower_outliers = f"{min_value}:{lower_outlier_bnd}:1"
    upper_outlier_bnd = upper_whisker + 0.000000000001
    upper_outliers = f"{upper_outlier_bnd}:{max_value}:1"
    if min_value < lower_whisker and max_value > upper_whisker:
        recode_rules = "{}\n{}".format(lower_outliers, upper_outliers)
    elif min_value < lower_whisker:
        recode_rules = lower_outliers
    elif max_value > upper_whisker:
        recode_rules = upper_outliers
    else:
        recode_rules = False

    # If outliers are asked for, extract their values
    if outliers and recode_rules:
        colname = strip_mapset(name)
        tmprast = create_temporary_name("tmp01")
        Module(
            "r.recode",
            input=name,
            output=tmprast,
            rules="-",
            stdin_=recode_rules,
        )
        vect_name = create_unique_name("tmp")
        Module("r.to.vect", input=tmprast, output=vect_name, type="point")
        Module("v.what.rast", map=vect_name, raster=name, column=colname)
        fliers = Module(
            "db.select", sql=f"select {colname} from {vect_name}", stdout_=PIPE
        ).outputs.stdout
        fliers = fliers.split("\n")[1:-1]
        fliers = [float(x) for x in fliers]

        # If asked for, save point vector layer
        if name_outliers_map:
            Module("v.db.dropcolumn", map=vect_name, columns=["value", "label"])
            Module("g.rename", vector=[vect_name, name_outliers_map])
            gs.message("Point vector map '{}' created".format(vect_name))
    elif outliers and not recode_rules:
        fliers = []
        gs.message("\n--> There are no outliers")
    else:
        fliers = []

    # Set plot dimensions and fontsize
    if dimensions:
        dimensions = [float(x) for x in dimensions.split(",")]
    else:
        if vertical:
            dimensions = [4, 8]
        else:
            dimensions = [8, 4]
    if fontsize:
        plt.rcParams["font.size"] = fontsize

    # Create plot
    _, ax = plt.subplots(figsize=dimensions)
    boxes = [
        {
            "label": strip_mapset(name),
            "whislo": lower_whisker,
            "q1": quantile_1,
            "med": quantile_2,
            "q3": quantile_3,
            "whishi": upper_whisker,
            "fliers": fliers,
            "cilo": lower_notch,
            "cihi": upper_notch,
        }
    ]
    ax.bxp(
        boxes,
        showfliers=True,
        widths=bxp_width,
        vert=vertical,
        shownotches=notch,
        flierprops={
            "marker": flier_marker,
            "markersize": flier_size,
            "markerfacecolor": flier_color,
            "markeredgecolor": flier_color,
        },
    )
    if vertical:
        ax.set_ylabel(strip_mapset(name))
        ax.axes.get_xaxis().set_visible(False)
    else:
        ax.set_xlabel(strip_mapset(name))
        ax.axes.get_yaxis().set_visible(False)
    if rotate_label:
        plt.xticks(rotation=90)
    if output:
        plt.savefig(output, bbox_inches="tight", dpi=dpi)
        plt.close()
    else:
        plt.tight_layout()
        plt.show()
        plt.close()


def bxp_zones(
    name,
    zones,
    outliers,
    output,
    dimensions,
    dpi,
    vertical,
    notch,
    rotate_label,
    sort,
    name_outliers_map,
    whisker_range,
    bpcolors,
    fontsize,
    show_catnumbers,
    bxp_width,
    flier_size,
    flier_marker,
    flier_color,
    plot_rast_stats,
    raster_stat_color,
    raster_stat_alpha,
):
    """Compute the statistics used to create the boxplot,
    and create the boxplots per zone from the zonal map."""

    # Get colors
    if bpcolors:
        # Get list with color rgb codes and corresponding category id
        zones_color = Module("r.colors.out", map=zones, stdout_=PIPE).outputs.stdout
        zones_color = zones_color.replace("\r", "").split("\n")
        zones_color = [_f for _f in zones_color if _f]
        zones_color = [
            _x
            for _x in zones_color
            if not _x.startswith("nv") and not _x.startswith("default")
        ]
        zones_colorids = [_y[0] for _y in [_x.split(" ") for _x in zones_color]]

        # Check if zonal map has a color table
        # (or rather, if the category values are integers)
        if not all([item.isdigit() for item in zones_colorids]):
            gs.fatal("The zonal map probably does not have a color table")
        zones_colorids = [int(_x) for _x in zones_colorids]

    # Get labels
    labels = Module(
        "r.category", map=zones, separator="pipe", stdout_=PIPE
    ).outputs.stdout
    labels = labels.replace("\r", "").split("\n")
    labels = [_f for _f in labels if _f]
    labels = [_y for _y in [_x.split("|") for _x in labels]]
    labelsids = [int(_z[0]) for _z in labels]
    labels = [_z[0] if len(_z[1]) == 0 else _z[1] for _z in labels]

    # Get colors (continuation)
    if bpcolors:

        # Select the actual raster categories and extract the rgb values
        zones_color = [
            zones_color[id]
            for id, _ in enumerate(zones_color)
            if zones_colorids[id] in labelsids
        ]
        zones_colorids = [_c for _c in zones_colorids if _c in labelsids]
        zones_color = [_y[1] for _y in [_x.split(" ") for _x in zones_color]]
        zones_color = [_z.split(":") for _z in zones_color]
        zones_rgb = [[int(_x) / 255 for _x in _y] for _y in zones_color]
        txt_rgb = []
        for i in zones_color:
            rgb_i = list(map(int, i))
            if rgb_i[0] * 0.299 + rgb_i[1] * 0.587 + rgb_i[2] * 0.114 > 149:
                txt_rgb.append([0, 0, 0, 0.7])
            else:
                txt_rgb.append([1, 1, 1, 0.7])

    # Compute statistics
    quantstats = Module(
        "r.stats.quantile",
        flags=["p", "t"],
        base=zones,
        cover=name,
        percentiles=[0, 25, 50, 75, 100],
        stdout_=PIPE,
    ).outputs.stdout
    quantstats = quantstats.replace("\r", "").split("\n")
    quantstats = [_f for _f in quantstats if _f]

    # Ordering boxplots
    order_bpl = [_x.split(":") for _x in quantstats[1:]]
    ids = []
    medians = []
    for zone_id, value in enumerate(order_bpl):
        ids.append(zone_id)
        medians.append(float(value[3]))
    if sort == "descending":
        ordered_list = [i for _, i in sorted(zip(medians, ids), reverse=True)]
    elif sort == "ascending":
        ordered_list = [i for _, i in sorted(zip(medians, ids), reverse=False)]
    else:
        ordered_list = list(range(0, len(order_bpl)))
    if bpcolors:
        zones_rgb[:] = [zones_rgb[i] for i in ordered_list]
        txt_rgb[:] = [txt_rgb[i] for i in ordered_list]

    # Define the boxes
    boxes = []
    vectornames = []

    # Construct per zone the boxplot
    for i in ordered_list:

        # Get boxplot label and stats
        if bool(show_catnumbers):
            zone_name = "{}) {}".format(labelsids[i], labels[i])
        else:
            zone_name = labels[i]
        quantstats_i = order_bpl[i]

        # Extract the stats to construct boxplot ith zone
        min_value = float(quantstats_i[1])
        quantile_1 = float(quantstats_i[2])
        quantile_2 = float(quantstats_i[3])
        quantile_3 = float(quantstats_i[4])
        max_value = float(quantstats_i[5])

        # Compute the iqr and limits whiskers
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

        # Compute, if requested, the notch limits
        if notch:
            univar = Module(
                "r.univar", flags=["g", "t"], map=name, stdout_=PIPE
            ).outputs.stdout
            n_values = int(univar.replace("\r", "").split("\n")[1].split("|")[0])
            lower_notch = quantile_2 - 1.57 * (iqr / n_values**2)
            upper_notch = quantile_2 + 1.57 * (iqr / n_values**2)
        else:
            lower_notch = ""
            upper_notch = ""

        # Construct recode rules to map outliers
        lower_outlier_bnd = lower_whisker - 0.000000000001
        lower_outliers = f"{min_value}:{lower_outlier_bnd}:1"
        upper_outlier_bnd = upper_whisker + 0.000000000001
        upper_outliers = f"{upper_outlier_bnd}:{max_value}:1"
        if min_value < lower_whisker and max_value > upper_whisker:
            recode_rules = "{}\n{}".format(lower_outliers, upper_outliers)
        elif min_value < lower_whisker:
            recode_rules = lower_outliers
        elif max_value > upper_whisker:
            recode_rules = upper_outliers
        else:
            recode_rules = False

        # Extract outliers values of ith zone
        if outliers and recode_rules:
            tmpname = create_temporary_name("tmp02")
            tmpvect = create_temporary_name("tmpvec02")
            Module(
                "r.recode",
                input=name,
                output=tmpname,
                rules="-",
                stdin_=recode_rules,
            )
            vectornames.append(tmpvect)
            # Set mask to select outlier cells
            Module("r.mask", raster=zones, maskcats=int(quantstats_i[0]))
            Module(
                "r.to.vect",
                input=tmpname,
                output=tmpvect,
                type="point",
            )
            Module("g.remove", type="raster", name=tmpname, flags="f")
            Module("r.mask", flags="r")
            # Get values input raster and write to outlier points
            colname = strip_mapset(name)
            Module("v.what.rast", map=tmpvect, raster=name, column=colname)
            fliers = Module(
                "db.select",
                sql=f"select {colname} from {tmpvect}",
                stdout_=PIPE,
            ).outputs.stdout
            fliers = list(set(fliers.split("\n")[1:-1]))
            fliers = [float(x) for x in fliers]
        else:
            fliers = []

        dict_i = {
            "label": zone_name,
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

    # Save outlier vector layer
    if name_outliers_map and vectornames:
        if len(vectornames) == 1:
            Module("g.rename", vector=[vectornames[0], name_outliers_map])
        else:
            Module(
                "v.patch",
                flags="e",
                input=vectornames,
                output=name_outliers_map,
            )
        Module(
            "v.db.dropcolumn",
            map=name_outliers_map,
            columns=["value", "label"],
        )
        colzones = strip_mapset(zones)
        Module("v.what.rast", map=name_outliers_map, raster=zones, column=colzones)
        gs.message("Point vector map '{}' created".format(name_outliers_map))
    elif name_outliers_map:
        gs.message("\n--> There are no outliers")

    # Remove intermediate layers
    if outliers and vectornames:
        Module("g.remove", type="vector", name=vectornames, flags="f")

    # Set plot dimensions and fontsize
    if dimensions:
        dimensions = [float(x) for x in dimensions.split(",")]
    else:
        if vertical:
            dimensions = [8, 4]
        else:
            dimensions = [4, 8]
    if fontsize:
        plt.rcParams["font.size"] = fontsize

    # Plot the figure
    _, ax = plt.subplots(figsize=dimensions)

    # Draw raster statistics
    rast_median_alpha = min(1, raster_stat_alpha + 0.1)
    if plot_rast_stats and vertical:
        _, quantile_1_r, quantile_2_r, quantile_3_r, _ = raster_stats(name=name)
        plot_rast_stats_l = plot_rast_stats.split(",")
        if "IQR" in plot_rast_stats_l:
            ax.axhspan(
                quantile_1_r,
                quantile_3_r,
                0,
                1,
                alpha=raster_stat_alpha,
                color=raster_stat_color,
                linewidth=0.5,
            )
        if "median" in plot_rast_stats_l:
            ax.axhline(
                quantile_2_r,
                color=raster_stat_color,
                linestyle="-",
                alpha=rast_median_alpha,
                linewidth=1,
            )
    elif plot_rast_stats:
        _, quantile_1_r, quantile_2_r, quantile_3_r, _ = raster_stats(name=name)
        plot_rast_stats_l = plot_rast_stats.split(",")
        if "IQR" in plot_rast_stats_l:
            ax.axvspan(
                quantile_1_r,
                quantile_3_r,
                0,
                1,
                alpha=raster_stat_alpha,
                color=raster_stat_color,
                linewidth=0.5,
            )
        if "median" in plot_rast_stats_l:
            ax.axvline(
                quantile_2_r,
                color=raster_stat_color,
                linestyle="-",
                alpha=rast_median_alpha,
                linewidth=1,
            )

    # Draw boxplots
    bxplot = ax.bxp(
        boxes,
        showfliers=True,
        widths=bxp_width,
        vert=vertical,
        shownotches=notch,
        patch_artist=bpcolors,
        flierprops={
            "marker": flier_marker,
            "markersize": flier_size,
            "markerfacecolor": flier_color,
            "markeredgecolor": flier_color,
        },
    )
    if bpcolors:
        for patch, color in zip(bxplot["boxes"], zones_rgb):
            patch.set_facecolor(color)
        for median, mcolor in zip(bxplot["medians"], txt_rgb):
            median.set_color(mcolor)
    if vertical:
        ax.set_ylabel(strip_mapset(name))
    else:
        ax.set_xlabel(strip_mapset(name))
    if rotate_label:
        plt.xticks(rotation=90)
    if output:
        plt.savefig(output, bbox_inches="tight", dpi=dpi)
        plt.close()
    else:
        plt.tight_layout()
        plt.show()
        plt.close()


def main(options, flags):
    """
    Draws the boxplot of raster values. Optionally, this is done per category
    of a zonal raster layer
    """

    global plt
    try:
        import matplotlib
        from matplotlib.colors import is_color_like

        matplotlib.use("WXAgg")
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("matplotlib is not installed"))

    # input
    value_raster = options["input"]
    zones_raster = options["zones"]
    if zones_raster:
        check_integer(zones_raster)
    if not flags["g"] and zones_raster:
        gs.use_temp_region()
        Module("g.region", raster=zones_raster)

    if not options["raster_stat_color"]:
        raster_stat_color = "grey"
    elif not ":" in options["raster_stat_color"]:
        raster_stat_color = options["raster_stat_color"]
    else:
        raster_stat_color = [
            int(_x) / 255 for _x in options["raster_stat_color"].split(":")
        ]
    if not is_color_like(raster_stat_color):
        gs.fatal(_("{} is not a valid color".format(options["raster_stat_color"])))

    # Create tmp input to get right categories and colors
    mask_present = checkmask()
    if mask_present:
        tmp_inputlayer = create_temporary_name("tmpinput")
        Module(
            "r.mapcalc",
            expression="{} = {}".format(tmp_inputlayer, zones_raster),
        )
        zones_raster = tmp_inputlayer
    output = options["output"]
    fontsize = options["fontsize"]
    bxp_width = options["boxplot_width"]
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
    if not is_color_like(flier_color):
        gs.fatal(_("{} is not a valid color".format(options["flier_color"])))
    if bool(bxp_width):
        bxp_width = float(bxp_width)
        if bxp_width > 1 or bxp_width <= 0:
            gs.fatal(_("The boxplot width needs to in the interval (0,1]"))
    elif zones_raster:
        bxp_width = 0.6
    else:
        bxp_width = 0.75
    if fontsize:
        fontsize = int(fontsize)
    else:
        fontsize = 10
    whisker_range = float(options["range"])
    bpcolor = flags["c"]
    show_catnumbers = flags["s"]
    if whisker_range <= 0:
        gs.fatal(_("The range value need to be larger than 0"))
    if flags["h"]:
        vertical = False
    else:
        vertical = True
    if options["dpi"]:
        dpi = float(options["dpi"])
    else:
        dpi = 300
    dimensions = options["plot_dimensions"]
    name_outliers_map = options["map_outliers"]
    sort = options["order"]
    outliers = flags["o"]
    rotate_label = flags["r"]
    print_notch = flags["n"]
    plot_rast_stats = options["raster_statistics"]
    if not zones_raster and plot_rast_stats:
        gs.warning(
            "No zonal layer was defined.\n"
            "Therefore, the option to plot the raster statistics is ignored"
        )

    # Plot boxplot(s)
    if zones_raster:
        bxp_zones(
            name=value_raster,
            zones=zones_raster,
            outliers=outliers,
            output=output,
            dimensions=dimensions,
            dpi=dpi,
            vertical=vertical,
            notch=print_notch,
            rotate_label=rotate_label,
            sort=sort,
            name_outliers_map=name_outliers_map,
            whisker_range=whisker_range,
            bpcolors=bpcolor,
            fontsize=fontsize,
            show_catnumbers=show_catnumbers,
            bxp_width=bxp_width,
            flier_size=flier_size,
            flier_marker=flier_marker,
            flier_color=flier_color,
            plot_rast_stats=plot_rast_stats,
            raster_stat_color=raster_stat_color,
            raster_stat_alpha=float(options["raster_stat_alpha"]),
        )
    else:
        bxp_nozones(
            name=value_raster,
            outliers=outliers,
            output=output,
            dimensions=dimensions,
            dpi=dpi,
            vertical=vertical,
            notch=print_notch,
            rotate_label=rotate_label,
            name_outliers_map=name_outliers_map,
            whisker_range=whisker_range,
            fontsize=fontsize,
            bxp_width=bxp_width,
            flier_size=flier_size,
            flier_marker=flier_marker,
            flier_color=flier_color,
        )


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
