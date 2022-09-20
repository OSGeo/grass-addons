#!/usr/bin/env python3

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
# % key: fontsize
# % type: integer
# % label: Font size
# % answer: 10
# % description: Default font size
# % guisection: Output
# % required: no
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
# % guisection: Output
# % required: no
# %end


# %flag
# % key: o
# % label: Include outliers
# % description: Draw boxplot(s) with outliers
# % guisection: Statistics
# %end

# %rules
# % requires: map_outliers, -o
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

# %option
# % key: bx_sort
# % type: string
# % label: Sort boxplots
# % description: Sort boxplots based on their median values
# % required: no
# % options: descending,ascending
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
# % key: s
# % label: Show category numbers
# % description: Show the category numbers of the zonal map
# % guisection: Plot format
# %end

# %option G_OPT_C
# % key: raster_stat_color
# % label: Color of the raster IQR and median
# % description: Color of raster IQR and median
# % required: no
# % answer: grey
# % guisection: Plot format
# %end

# %option
# % key: raster_stat_alpha
# % type: double
# % description: Transparency of the raster IQR band
# % required: no
# % options: 0-1
# % answer: 0.2
# % guisection: Plot format
# %end

# %rules
# % requires: raster_statistics, zones
# %end

# %option G_OPT_CN
# % key: bx_color
# % label: Color of the boxplots
# % description: Color of boxplots
# % required: no
# % answer: white
# % guisection: Boxplot format
# %end

# %flag
# % key: c
# % label: Zonal colors
# % description: Color boxploxs using the colors of the categories of the zonal raster
# % guisection: Boxplot format
# %end

# %rules
# % requires: -c, zones
# %end

# %rules
# % excludes: -c, bx_color
# %end

# %option
# % key: bx_width
# % type: double
# % label: Boxplot width
# % description: The width of the boxplots (0,1])
# % required: no
# % guisection: Boxplot format
# % answer: 0.75
# % options: 0-1
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

# %rules
# % excludes: -c, median_color
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

# %rules
# % requires: -s, zones
# %end


import atexit
import sys
import uuid
from subprocess import PIPE

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


def check_integer(name):
    """Check if map values are integer

    :param str name: name zonal map

    :return str: no return if map is of type integer, otherwise error message
    """
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


def checkmask():
    """Check if there is a MASK set

    :return bool: true (mask present) or false (mask not present)
    """
    ffile = gs.find_file(name="MASK", element="cell", mapset=gs.gisenv()["MAPSET"])
    mask_presence = ffile["name"] == "MASK"
    return mask_presence


def check_regionraster_match(raster):
    gregion = gs.region()
    rregion = gs.parse_command("r.info", flags="g", map=raster)
    reg_matches_rast = all(
        [
            gregion["rows"] == int(rregion["rows"]),
            gregion["nsres"] == float(rregion["nsres"]),
            gregion["ewres"] == float(rregion["ewres"]),
            gregion["s"] == float(rregion["south"]),
            gregion["n"] == float(rregion["north"]),
            gregion["e"] == float(rregion["east"]),
            gregion["w"] == float(rregion["west"]),
        ]
    )
    return reg_matches_rast


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


def bx_labels(zones):
    """Get the category labels of the zonal map

    :param str zones: name of the zonal map

    :return list labels: list with labels
    :return list labelsids: list of ids of the zonal map categories

    """
    labels = Module(
        "r.category", map=zones, separator="pipe", stdout_=PIPE
    ).outputs.stdout
    labels = labels.replace("\r", "").split("\n")
    labels = [_f for _f in labels if _f]
    labels = [_y for _y in [_x.split("|") for _x in labels]]
    labelsids = [int(_z[0]) for _z in labels]
    labels = [_z[0] if len(_z[1]) == 0 else _z[1] for _z in labels]
    return labels, labelsids


def get_zonalcolors(zones, labelsids):
    """Get the colors of the categories of the zonal map

    :param str zones: name of the zonal map
    :param list labelsids: list of the category ids

    :return list zones_rgb: list rgb codes for zones
    :return list txt_rgb: list rgb codes for median line

    """
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
    return zones_rgb, txt_rgb


def bx_zonal_stats(zones, name, bx_sort):
    """Compute the zonal stats to construct the boxplot (and order boxplots)

    :param str zones: name of the zonal map
    :param str name: name of the value map

    :return list quantstats: matrix of zonal stats
    :return list ordered_list: list with the order of the boxplots

    """
    # Compute quantiles and min and max values
    quantstats_str = Module(
        "r.stats.quantile",
        flags=["p", "t"],
        base=zones,
        cover=name,
        percentiles=[0, 25, 50, 75, 100],
        stdout_=PIPE,
    ).outputs.stdout
    quantstats_str = quantstats_str.replace("\r", "").split("\n")
    quantstats_str = [_f for _f in quantstats_str if _f]

    # Ordering boxplots
    quantstats = [list(map(float, _x.split(":"))) for _x in quantstats_str[1:]]
    ids = []
    medians = []
    for zone_id, value in enumerate(quantstats):
        ids.append(zone_id)
        medians.append(float(value[3]))
    if bx_sort == "descending":
        ordered_list = [i for _, i in sorted(zip(medians, ids), reverse=True)]
    elif bx_sort == "ascending":
        ordered_list = [i for _, i in sorted(zip(medians, ids), reverse=False)]
    else:
        ordered_list = list(range(0, len(quantstats)))
    return quantstats, ordered_list


def get_bx_stats(quantstats_i, whisker_range):
    """Compute the zonal stats to construct the boxplot (and order boxplots)

    :param list quantstats: nested list with boxplot stats
    :param float whisker_range: wisker range

    :return list: list with minimum value, 1st, 2nd and 3rd
                  quantiles and maximum value of the input raster

    """
    # Extract the stats to construct boxplot ith zone
    min_value = quantstats_i[1]
    quant1 = quantstats_i[2]
    quant2 = quantstats_i[3]
    quant3 = quantstats_i[4]
    max_value = quantstats_i[5]

    # Compute the iqr and limits whiskers
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


def compute_outliers(
    rastername,
    min_value,
    max_value,
    lower_whisker,
    upper_whisker,
    vectornames,
    quantstats_i,
    outliers,
    zones,
):
    """Compute outliers

    :param str raster: name value raster
    :param float min_value: min value value raster
    :param float max_value: min value value raster
    :param float lower_whisker: lower whisker value raster
    :param float upper_whisker: upper whisker value raster
    :param list vectornames: list with vectorlayers of outliers
    :param list quanstats_i: list with stats for zone i
    :param bool outlier: create vector map of outliers (true or false)
    :param bool zones: zonal map included or not

    :return list: list with outlier values for input raster
    :return list vectornames: list with vectorlayers of outliers
    """

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
    if bool(outliers) and bool(recode_rules):
        if bool(zones):
            Module("r.mask", raster=zones, maskcats=int(quantstats_i[0]))
        tmpname = create_temporary_name("tmp02")
        tmpvect = create_temporary_name("tmpvec02")
        Module(
            "r.recode",
            input=rastername,
            output=tmpname,
            rules="-",
            stdin_=recode_rules,
        )
        vectornames.append(tmpvect)
        Module(
            "r.to.vect",
            input=tmpname,
            output=tmpvect,
            type="point",
        )
        Module("g.remove", type="raster", name=tmpname, flags="f")
        if zones:
            Module("r.mask", flags="r")

        # Get values input raster and write to outlier points
        colname = strip_mapset(rastername)
        Module("v.what.rast", map=tmpvect, raster=rastername, column=colname)
        fliers = Module(
            "db.select",
            sql=f"select {colname} from {tmpvect}",
            stdout_=PIPE,
        ).outputs.stdout
        fliers = list(set(fliers.split("\n")[1:-1]))
        fliers = [float(x) for x in fliers]
    else:
        fliers = []
    return fliers, vectornames


def bxp_nozones_stats(rastername, whisker_range):
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


def bxp_nozones(opt):
    """Compute the statistics used to create the boxplot,
    and create the boxplot. This function is used in case
    no zonal raster is provided.

    :param dict opt: dictionary with the input variables/objects
    """

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
    ) = bxp_nozones_stats(opt["value_raster"], opt["whisker_range"])

    # Compute notch limits
    if bool(opt["notch"]):
        lower_notch, upper_notch = compute_notch(opt["value_raster"], quant2, iqr)
    else:
        lower_notch = upper_notch = ""

    # Compute outliers
    if bool(opt["outliers"]):
        fliers, vect_name = compute_outliers(
            opt["value_raster"],
            min_value,
            max_value,
            lower_whisker,
            upper_whisker,
            [],
            [],
            opt["outliers"],
            False,
        )
    else:
        fliers = []

    if opt["name_outliers_map"] and bool(fliers):
        print(vect_name)
        Module("v.db.dropcolumn", map=vect_name[0], columns=["value", "label"])
        Module("g.rename", vector=[vect_name[0], opt["name_outliers_map"]])
        gs.message("Point vector map '{}' created".format(opt["name_outliers_map"]))

    # Create plot
    _, ax = plt.subplots(figsize=opt["dimensions"])
    boxes = [
        {
            "label": strip_mapset(opt["value_name"]),
            "whislo": lower_whisker,
            "q1": quant1,
            "med": quant2,
            "q3": quant3,
            "whishi": upper_whisker,
            "fliers": fliers,
            "cilo": lower_notch,
            "cihi": upper_notch,
        }
    ]
    boxprops = dict(linewidth=opt["bxp_linewidth"], facecolor=opt["bx_color"])
    whiskerprops = dict(linewidth=opt["whisker_linewidth"])
    medianprops = dict(linewidth=opt["median_lw"], color=opt["median_color"])
    ax.bxp(
        boxes,
        showfliers=True,
        widths=opt["bxp_width"],
        vert=opt["vertical"],
        shownotches=bool(opt["notch"]),
        boxprops=boxprops,
        whiskerprops=whiskerprops,
        medianprops=medianprops,
        patch_artist=True,
        capprops=whiskerprops,
        flierprops={
            "marker": opt["flier_marker"],
            "markersize": opt["flier_size"],
            "markerfacecolor": opt["flier_color"],
            "markeredgecolor": opt["flier_color"],
        },
    )

    # Labels
    if bool(opt["vertical"]):
        ax.set_ylabel(strip_mapset(opt["value_name"]))
        ax.axes.get_xaxis().set_visible(False)
    else:
        ax.set_xlabel(strip_mapset(opt["value_name"]))
        ax.axes.get_yaxis().set_visible(False)

    # Label orientation
    if bool(opt["rotate_labels"]) and opt["vertical"]:
        rotate_labels = float(opt["rotate_labels"])
        if abs(rotate_labels) <= 10 or abs(rotate_labels) >= 80:
            plt.xticks(rotation=rotate_labels)
        elif rotate_labels < 0:
            plt.xticks(rotation=rotate_labels, ha="left", rotation_mode="anchor")
        else:
            plt.xticks(rotation=rotate_labels, ha="right", rotation_mode="anchor")
    elif bool(opt["rotate_labels"]) and not bool(opt["vertical"]):
        rotate_labels = float(opt["rotate_labels"])
        if abs(rotate_labels) <= 10 or abs(rotate_labels) >= 80:
            plt.yticks(rotation=rotate_labels)
        else:
            plt.yticks(rotation=rotate_labels, ha="right", rotation_mode="anchor")
    elif bool(opt["vertical"]):
        plt.xticks(rotation=45, ha="right", rotation_mode="anchor")

    # Output
    if bool(opt["output"]):
        plt.savefig(opt["output"], bbox_inches="tight", dpi=opt["dpi"])
        plt.close()
    else:
        plt.tight_layout()
        plt.show()
        plt.close()


def bxp_zones(opt):
    """Compute the statistics used to create the boxplot,
    and create the boxplot. This function is used in case
    no zonal raster is provided.

    :param dict opt: dictionary with the input variables/objects
    """
    # Get labels
    labels, labelsids = bx_labels(opt["zones_raster"])

    # Get colors
    if opt["bx_zonalcolors"]:
        zones_rgb, txt_rgb = get_zonalcolors(opt["zones_raster"], labelsids)

    # Compute statistics
    quantstats, ordered_list = bx_zonal_stats(
        opt["zones_raster"], opt["value_raster"], opt["bx_sort"]
    )

    # Change the order of the colors of the boxplots and median to match the
    # order in which the boxplots will be plottted
    if opt["bx_zonalcolors"]:
        zones_rgb[:] = [zones_rgb[i] for i in ordered_list]
        txt_rgb[:] = [txt_rgb[i] for i in ordered_list]

    # Define the boxes
    boxes = []
    vectornames = []

    # Construct per zone the boxplot
    for i in ordered_list:

        # Get stats for the ith boxplot
        (
            min_value,
            quant1,
            quant2,
            quant3,
            max_value,
            iqr,
            lower_whisker,
            upper_whisker,
        ) = get_bx_stats(quantstats[i], opt["whisker_range"])

        # Compute notch limits
        if opt["notch"]:
            lower_notch, upper_notch = compute_notch(opt["value_raster"], quant2, iqr)
        else:
            lower_notch = upper_notch = ""

        # Compute outliers
        if opt["outliers"]:
            fliers, vectornames = compute_outliers(
                opt["value_raster"],
                min_value,
                max_value,
                lower_whisker,
                upper_whisker,
                vectornames,
                quantstats[i],
                opt["outliers"],
                opt["zones_raster"],
            )
        else:
            fliers = []

        # Construct box
        # Get boxplot label and stats
        if bool(opt["show_catnumbers"]):
            zone_name = "{}) {}".format(labelsids[i], labels[i])
        else:
            zone_name = labels[i]

        dict_i = {
            "label": zone_name,
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

    # Save outlier vector layer
    if bool(opt["name_outliers_map"]) and bool(vectornames):
        if len(vectornames) == 1:
            Module("g.rename", vector=[vectornames[0], opt["name_outliers_map"]])
        else:
            Module(
                "v.patch",
                flags="e",
                input=vectornames,
                output=opt["name_outliers_map"],
            )
        Module(
            "v.db.dropcolumn",
            map=opt["name_outliers_map"],
            columns=["value", "label"],
        )
        colzones = strip_mapset(opt["zones_name"])
        Module(
            "v.what.rast",
            map=opt["name_outliers_map"],
            raster=opt["zones_raster"],
            column=colzones,
        )
        gs.message("Point vector map '{}' created".format(opt["name_outliers_map"]))
    elif bool(opt["name_outliers_map"]):
        gs.message("\n--> There are no outliers B")

    # Remove intermediate layers
    if opt["outliers"] and vectornames:
        Module("g.remove", type="vector", name=vectornames, flags="f")

    # Set plot dimensions and fontsize
    if bool(opt["fontsize"]):
        plt.rcParams["font.size"] = opt["fontsize"]

    # Plot the figure
    _, ax = plt.subplots(figsize=opt["dimensions"])

    # Draw raster statistics
    rast_median_alpha = min(1, opt["raster_stat_alpha"] + 0.1)
    if bool(opt["plot_rast_stats"]) and bool(opt["vertical"]):
        _, quant1_r, quant2_r, quant3_r, _ = raster_stats(name=opt["value_raster"])
        plot_rast_stats_l = opt["plot_rast_stats"].split(",")
        if "IQR" in plot_rast_stats_l:
            ax.axhspan(
                quant1_r,
                quant3_r,
                0,
                1,
                alpha=opt["raster_stat_alpha"],
                color=opt["raster_stat_color"],
                linewidth=0.5,
            )
        if "median" in plot_rast_stats_l:
            ax.axhline(
                quant2_r,
                color=opt["raster_stat_color"],
                linestyle="-",
                alpha=rast_median_alpha,
                linewidth=opt["median_lw"],
            )
    elif bool(opt["plot_rast_stats"]):
        _, quant1_r, quant2_r, quant3_r, _ = raster_stats(name=opt["value_raster"])
        plot_rast_stats_l = opt["plot_rast_stats"].split(",")
        if "IQR" in plot_rast_stats_l:
            ax.axvspan(
                quant1_r,
                quant3_r,
                0,
                1,
                alpha=opt["raster_stat_alpha"],
                color=opt["raster_stat_color"],
                linewidth=0.5,
            )
        if "median" in plot_rast_stats_l:
            ax.axvline(
                quant2_r,
                color=opt["raster_stat_color"],
                linestyle="-",
                alpha=rast_median_alpha,
                linewidth=opt["median_lw"],
            )

    # Draw boxplots
    boxprops = dict(linewidth=opt["bxp_linewidth"], facecolor=opt["bx_color"])
    whiskerprops = dict(linewidth=opt["whisker_linewidth"])
    medianprops = dict(linewidth=opt["median_lw"], color=opt["median_color"])
    bxplot = ax.bxp(
        boxes,
        showfliers=True,
        widths=opt["bxp_width"],
        vert=bool(opt["vertical"]),
        shownotches=bool(opt["notch"]),
        patch_artist=True,
        boxprops=boxprops,
        medianprops=medianprops,
        whiskerprops=whiskerprops,
        capprops=whiskerprops,
        flierprops={
            "marker": opt["flier_marker"],
            "markersize": opt["flier_size"],
            "markerfacecolor": opt["flier_color"],
            "markeredgecolor": opt["flier_color"],
        },
    )

    # Boxplots get colors matching category colors zonal map
    if bool(opt["bx_zonalcolors"]):
        for patch, color in zip(bxplot["boxes"], zones_rgb):
            patch.set_facecolor(color)
        for median, mcolor in zip(bxplot["medians"], txt_rgb):
            median.set_color(mcolor)

    # Labels
    if bool(opt["vertical"]):
        ax.set_ylabel(strip_mapset(opt["value_name"]))
    else:
        ax.set_xlabel(strip_mapset(opt["value_name"]))

    # Label orientation
    if bool(opt["rotate_labels"]) and opt["vertical"]:
        rotate_labels = float(opt["rotate_labels"])
        if abs(rotate_labels) <= 10 or abs(rotate_labels) >= 80:
            plt.xticks(rotation=rotate_labels)
        elif rotate_labels < 0:
            plt.xticks(rotation=rotate_labels, ha="left", rotation_mode="anchor")
        else:
            plt.xticks(rotation=rotate_labels, ha="right", rotation_mode="anchor")
    elif bool(opt["rotate_labels"]) and not bool(opt["vertical"]):
        rotate_labels = float(opt["rotate_labels"])
        if abs(rotate_labels) <= 10 or abs(rotate_labels) >= 80:
            plt.yticks(rotation=rotate_labels)
        else:
            plt.yticks(rotation=rotate_labels, ha="right", rotation_mode="anchor")
    elif bool(opt["vertical"]):
        plt.xticks(rotation=45, ha="right", rotation_mode="anchor")

    # Output
    if bool(opt["output"]):
        plt.savefig(opt["output"], bbox_inches="tight", dpi=opt["dpi"])
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

    # lazy import matplotlib
    lazy_import_py_modules()

    # Check if zonal map is an integer map
    if options["zones"]:
        check_integer(options["zones"])

    # Output options
    dpi, dimensions, vertical = get_output_options(
        options["dpi"], options["plot_dimensions"], flags["h"]
    )

    # boxplot parameters
    bxp_width = float(options["bx_width"])
    if bxp_width == 0:
        gs.fatal(_("The boxplot width needs to be larger than 0"))
    bx_color = get_valid_color(options["bx_color"])
    median_color = get_valid_color(options["median_color"])

    # Whisker parameters
    whisker_range = float(options["range"])
    if whisker_range <= 0:
        gs.fatal(_("The range value need to be larger than 0"))

    # raster stats
    raster_stat_color = get_valid_color(options["raster_stat_color"])

    # Create new value rasters if there is a mask or the value raster
    # extent and resolution do not match that of the current region
    if bool(options["zones"]):
        mask_present = checkmask()
        valueraster_region = check_regionraster_match(options["input"])
        if mask_present or not valueraster_region:
            value_raster = create_temporary_name("tmpinput")
            Module(
                "r.mapcalc", expression="{} = {}".format(value_raster, options["input"])
            )
        else:
            value_raster = options["input"]

    # Create temporary zonal rasters if there is a mask or the zonal raster
    # extent and resolution do not match that of the current region
    if bool(options["zones"]):
        zonalraster_region = check_regionraster_match(options["zones"])
        if mask_present or not zonalraster_region:
            zonal_raster = create_temporary_name("tmpinput")
            Module(
                "r.mapcalc", expression="{} = {}".format(zonal_raster, options["zones"])
            )
        else:
            zonal_raster = options["zones"]

        # Remove mask (save temp backup)
        if mask_present:
            backup_mask = create_temporary_name("maskbackup")
            Module("g.rename", raster=["MASK", backup_mask])

    # Collect options
    base_options = {
        "value_name": options["input"],
        "value_raster": value_raster,
        "output": options["output"],
        "outliers": flags["o"],
        "notch": flags["n"],
        "name_outliers_map": options["map_outliers"],
        "fontsize": float(options["fontsize"]),
        "rotate_labels": options["rotate_labels"],
        "dimensions": dimensions,
        "dpi": dpi,
        "vertical": vertical,
        "bxp_linewidth": float(options["bx_lw"]),
        "bxp_width": bxp_width,
        "bx_color": bx_color,
        "whisker_linewidth": float(options["whisker_linewidth"]),
        "whisker_range": whisker_range,
        "flier_size": int(options["flier_size"]),
        "flier_marker": options["flier_marker"],
        "flier_color": get_valid_color(color=options["flier_color"]),
        "mask_present": mask_present,
        "median_lw": float(options["median_lw"]),
        "median_color": median_color,
    }
    if bool(options["zones"]):
        zone_options = {
            **base_options,
            **{
                "zones_name": options["zones"],
                "zones_raster": zonal_raster,
                "show_catnumbers": flags["s"],
                "bx_zonalcolors": flags["c"],
                "bx_sort": options["bx_sort"],
                "plot_rast_stats": options["raster_statistics"],
                "raster_stat_color": raster_stat_color,
                "raster_stat_alpha": float(options["raster_stat_alpha"]),
            },
        }

    # Closing message
    if not options["output"]:
        gs.message(
            _("\n> Note, you need to close the figure to finish the script \n\n")
        )

    # Plot boxplot(s)
    if bool(options["zones"]):
        bxp_zones(zone_options)
    else:
        bxp_nozones(base_options)

    # Restore original mask
    if mask_present and bool(options["zones"]):
        Module("g.rename", raster=[backup_mask, "MASK"])


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
