#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.boxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws boxplot(s) of raster values of the input raster.
#               Optionally, this can be done per category of a zonal map.
#
# SPDX-FileCopyrightText: 2022-2026 Paulo van Breugel
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
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
# % guisection: Input
# % required: yes
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
# % key: order
# % type: string
# % label: Sort boxplots
# % description: Sort boxplots based on their median values
# % required: no
# % options: descending,ascending
# % guisection: Plot format
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
# % description: Color of raster IQR and median.
# % required: no
# % answer:
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

# %option G_OPT_CN
# % key: box_color
# % label: Color of the boxplots
# % description: Fill color of the boxplots. Unset leaves the boxes unfilled (Matplotlib default).
# % required: no
# % answer:
# % guisection: Boxplot format
# %end

# %flag
# % key: c
# % label: Zonal colors
# % description: Color boxploxs using the colors of the categories of the zonal raster
# % guisection: Boxplot format
# %end

# %option
# % key: area_label
# % type: string
# % description: Show the area above each boxplot
# % required: no
# % options: m2,ha,km2,acres,mi2
# % guisection: Boxplot format
# %end

# %option
# % key: box_width
# % type: double
# % label: Boxplot width
# % description: The width of the boxplots (0,1]).
# % required: no
# % guisection: Boxplot format
# % options: 0-1
# %end

# %option
# % key: box_width_variable
# % type: string
# % description: Set the width of the boxplots proportional to the area of the zones (linear) or the square root of the zones (sqrt).
# % required: no
# % options: linear,sqrt
# % guisection: Boxplot format
# %end

# %option
# % key: box_linewidth
# % type: double
# % label: boxplot linewidth
# % description: The linewidth of the boxplots. Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
# %end

# %option
# % key: median_linewidth
# % type: double
# % description: width of the boxplot median line. Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
# %end

# %option G_OPT_C
# % key: median_color
# % label: Color of the boxlot median line
# % description: Color of median. Defaults to the Matplotlib default.
# % required: no
# % answer:
# % guisection: Boxplot format
# %end

# %option
# % key: whisker_linewidth
# % type: double
# % label: Whisker and cap linewidth
# % description: The linewidth of the whiskers and caps. Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
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
# % description: Set the flier size. Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
# %end

# %option G_OPT_C
# % key: flier_color
# % label: Flier color
# % description: Set the flier color. Defaults to the Matplotlib default.
# % required: no
# % answer:
# % guisection: Boxplot format
# %end

# %option
# % key: nprocs
# % type: integer
# % label: Number of threads for parallel computing
# % description: Number of threads used by r.univar when computing notch statistics (requires -n).
# % required: no
# % answer: 1
# %end

# %rules
# % requires: -c, zones
# % requires: -s, zones
# % requires: area_label, zones
# % requires: raster_statistics, zones
# % requires: box_width_variable, zones
# %end

import atexit
import sys
import uuid
from subprocess import PIPE

import grass.script as gs
from grass.pygrass.modules import Module

clean_maps = []
mask_backup_name = None


def lazy_import_py_modules(backend):
    """Lazy import Py modules"""
    global mpl
    global plt

    # lazy import matplotlib
    try:
        import matplotlib as mpl

        if backend is None:
            mpl.use("WXAgg")
        else:
            mpl.use("Agg")
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


def restore_mask_backup():
    """Best-effort restore of MASK from the tracked backup.

    On success, clears mask_backup_name. On failure, leaves it set and emits a
    warning with the backup name so the user can restore manually. Never raises.
    """
    global mask_backup_name
    if mask_backup_name is None:
        return
    mapset = gs.gisenv()["MAPSET"]
    found = gs.find_file(name=mask_backup_name, element="raster", mapset=mapset)
    if not found["file"]:
        mask_backup_name = None
        return
    try:
        # A MASK present here was created by r.boxplot itself (for example a
        # temporary zonal mask left behind by a failure), so remove it first
        # so the original can be renamed back from the backup.
        leftover = gs.find_file(name="MASK", element="cell", mapset=mapset)
        if leftover["file"]:
            Module("g.remove", flags="f", type="raster", name="MASK", quiet=True)
        Module("g.rename", raster=[mask_backup_name, "MASK"], quiet=True)
        mask_backup_name = None
    except Exception as exc:
        gs.warning(
            _(
                "Failed to restore MASK from backup <{name}>: {err}. "
                "Restore manually with: g.rename raster={name},MASK"
            ).format(name=mask_backup_name, err=exc)
        )


def cleanup():
    """Restore the original MASK if needed, then remove temporary maps"""
    restore_mask_backup()
    mapset = gs.gisenv()["MAPSET"]
    maps = reversed(clean_maps)
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
    if not mpl.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.").format(color))
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


def bx_zonal_stats(zones, name, order):
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
        separator="pipe",
        stdout_=PIPE,
    ).outputs.stdout
    quantstats_str = quantstats_str.replace("\r", "").split("\n")
    quantstats_str = [_f for _f in quantstats_str if _f]

    # Ordering boxplots
    quantstats = [list(map(float, _x.split("|"))) for _x in quantstats_str[1:]]
    ids = []
    medians = []
    for zone_id, value in enumerate(quantstats):
        ids.append(zone_id)
        medians.append(float(value[3]))
    if order == "descending":
        ordered_list = [i for _, i in sorted(zip(medians, ids), reverse=True)]
    elif order == "ascending":
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


def notch_limits(quant2, iqr, n_values):
    """Compute the lower and upper notch limits from a cell count.

    The notch is the 95% confidence interval of the median, approximated as
    median +/- 1.57 * IQR / sqrt(n), where n is the number of (non-null) cells
    the boxplot is based on.

    :param float quant2: 2nd quantile (median)
    :param float iqr: interquartile range
    :param int n_values: number of non-null cells

    :return list: list with lower and upper notch value
    """
    half_width = 1.57 * (iqr / n_values**0.5)
    return [quant2 - half_width, quant2 + half_width]


def raster_ncells(rastername, nprocs=1):
    """Return the number of non-null cells of a raster via r.univar.

    Used for the no-zones notch. Uses r.univar shell output (key=value) and
    reads the 'n' key, which is robust to field-order and separator changes
    and avoids combining the -g and -t flags (rejected by GRASS 8.5). Honors
    nprocs where r.univar supports it; note that r.univar disables
    parallelization when a MASK is active, so on the no-zones path (where a
    user MASK may be in place) nprocs may have no effect.

    :param str rastername: name of input raster
    :param int nprocs: number of threads for r.univar

    :return int: number of non-null cells
    """
    kwargs = {}
    if nprocs and nprocs > 1:
        kwargs["nprocs"] = nprocs
    # flags="g" (shell style) yields key=value lines parsed into a dict; "n"
    # is the non-null cell count.
    stats = gs.parse_command("r.univar", flags="g", map=rastername, **kwargs)
    return int(stats["n"])


def compute_notch(rastername, quant2, iqr, nprocs=1):
    """Compute notches of a boxplot for the whole input raster.

    Used on the no-zones path. The cell count is obtained from r.univar over
    the (possibly masked) input raster.

    :param str rastername: name of input raster
    :param float quant2: 2nd quantile
    :param float iqr: interquartile range
    :param int nprocs: number of threads for r.univar

    :return list: list with lower and upper notch value of input raster
    """
    n_values = raster_ncells(rastername, nprocs=nprocs)
    return notch_limits(quant2, iqr, n_values)


def zonal_ncells(zones, name, nprocs=1):
    """Return the non-null cell count per zone as a {category: n} dict.

    Computed in a single r.univar -t pass over the value raster with the
    zonal raster as zones, so the count is correct *per zone*.

    :param str zones: name of the zonal (base) raster
    :param str name: name of the value (cover) raster
    :param int nprocs: number of threads for r.univar

    :return dict: mapping of zone category (int) to non-null cell count (int)
    """
    kwargs = {}
    if nprocs and nprocs > 1:
        kwargs["nprocs"] = nprocs
    raw = Module(
        "r.univar",
        flags="t",
        map=name,
        zones=zones,
        separator="pipe",
        stdout_=PIPE,
        **kwargs,
    ).outputs.stdout
    lines = [ln for ln in raw.replace("\r", "").split("\n") if ln]
    counts = {}
    if not lines:
        return counts
    # First line is the header. Resolve column indices by name, falling back
    # to the documented positions (zone=0, non_null_cells=2) if the header is
    # not as expected.
    header = lines[0].split("|")
    try:
        zone_idx = header.index("zone")
        n_idx = header.index("non_null_cells")
    except ValueError:
        zone_idx, n_idx = 0, 2
    for ln in lines[1:]:
        fields = ln.split("|")
        zone_cat = int(fields[zone_idx])
        counts[zone_cat] = int(fields[n_idx])
    return counts


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
        try:
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
                quiet=True,
            )
            vectornames.append(tmpvect)
            Module(
                "r.to.vect",
                input=tmpname,
                output=tmpvect,
                type="point",
                quiet=True,
            )
            Module("g.remove", type="raster", name=tmpname, flags="f")
        finally:
            # Always remove the temporary zonal mask, even if the steps above
            # raise, so it is not left behind for cleanup() to trip over when
            # it tries to restore the original MASK from the backup. Guard with
            # a presence check.
            if zones:
                mapset = gs.gisenv()["MAPSET"]
                if gs.find_file(name="MASK", element="cell", mapset=mapset)["file"]:
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


def build_bxp_kwargs(opt, widths=None, patch_artist=None):
    """Build the ax.bxp keyword arguments, omitting appearance options that
    were left unset so they fall back to the Matplotlib/style defaults.

    :param dict opt: dictionary with the input variables/objects
    :param widths: boxplot width(s), omitted when None
    :param bool patch_artist: force patch_artist; defaults to True only when a
                              fill color is set

    :return dict: keyword arguments for ax.bxp
    """
    boxprops = {}
    if opt["bxp_linewidth"] is not None:
        boxprops["linewidth"] = opt["bxp_linewidth"]
    if opt["bx_color"] is not None:
        boxprops["facecolor"] = opt["bx_color"]
    whiskerprops = {}
    if opt["whisker_linewidth"] is not None:
        whiskerprops["linewidth"] = opt["whisker_linewidth"]
    medianprops = {}
    if opt["median_lw"] is not None:
        medianprops["linewidth"] = opt["median_lw"]
    if opt["median_color"] is not None:
        medianprops["color"] = opt["median_color"]
    flierprops = {"marker": opt["flier_marker"]}
    if opt["flier_size"] is not None:
        flierprops["markersize"] = opt["flier_size"]
    if opt["flier_color"] is not None:
        flierprops["markerfacecolor"] = opt["flier_color"]
        flierprops["markeredgecolor"] = opt["flier_color"]
    if patch_artist is None:
        patch_artist = opt["bx_color"] is not None
    kwargs = {
        "showfliers": True,
        "vert": bool(opt["vertical"]),
        "shownotches": bool(opt["notch"]),
        "patch_artist": patch_artist,
        "boxprops": boxprops,
        "medianprops": medianprops,
        "whiskerprops": whiskerprops,
        "capprops": whiskerprops,
        "flierprops": flierprops,
    }
    if widths is not None:
        kwargs["widths"] = widths
    return kwargs


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
        lower_notch, upper_notch = compute_notch(
            opt["value_raster"], quant2, iqr, nprocs=opt.get("nprocs", 1)
        )
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
    ax.bxp(boxes, **build_bxp_kwargs(opt, widths=opt["bxp_width"]))

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
        opt["zones_raster"], opt["value_raster"], opt["order"]
    )

    if opt["notch"]:
        zone_counts = zonal_ncells(
            opt["zones_raster"], opt["value_raster"], nprocs=opt.get("nprocs", 1)
        )
    else:
        zone_counts = {}

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
            zone_cat = int(quantstats[i][0])
            n_zone = zone_counts.get(zone_cat)
            if n_zone and n_zone > 0:
                lower_notch, upper_notch = notch_limits(quant2, iqr, n_zone)
            else:
                # Fallback: no count for this zone (should not normally happen);
                # skip the notch rather than emit a wrong or div-by-zero value.
                lower_notch = upper_notch = ""
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
    if bool(opt["plot_rast_stats"]):
        _, quant1_r, quant2_r, quant3_r, _ = raster_stats(name=opt["value_raster"])
        plot_rast_stats_l = opt["plot_rast_stats"].split(",")
        span_fn = ax.axhspan if opt["vertical"] else ax.axvspan
        line_fn = ax.axhline if opt["vertical"] else ax.axvline
        span_kwargs = {"alpha": opt["raster_stat_alpha"], "linewidth": 0.5}
        line_kwargs = {"linestyle": "-", "alpha": rast_median_alpha}
        if opt["raster_stat_color"] is not None:
            span_kwargs["color"] = opt["raster_stat_color"]
            line_kwargs["color"] = opt["raster_stat_color"]
        if opt["median_lw"] is not None:
            line_kwargs["linewidth"] = opt["median_lw"]
        if "IQR" in plot_rast_stats_l:
            span_fn(quant1_r, quant3_r, 0, 1, **span_kwargs)
        if "median" in plot_rast_stats_l:
            line_fn(quant2_r, **line_kwargs)

    # Draw boxplots
    if opt.get("variable_box_width") or opt.get("area_label"):
        # Compute area (number of cells) per zone for width scaling
        areas_cats = Module(
            "r.stats",
            flags="cna",
            separator="pipe",
            input=opt["zones_raster"],
            stdout_=PIPE,
        ).outputs.stdout.splitlines()
        areas_dict = {
            int(line.split("|")[0]): float(line.split("|")[1]) for line in areas_cats
        }
        ordered_ids = [labelsids[i] for i in ordered_list]

    if opt.get("variable_box_width"):
        zone_areas = [areas_dict.get(zid, 1) for zid in ordered_ids]

        # Use sqrt of areas if selected
        if opt.get("variable_box_width") == "sqrt":
            zone_areas = [a**0.5 for a in zone_areas]

        total_area = sum(zone_areas)
        raw_widths = [(a / total_area) for a in zone_areas]

        # Scale to max width = bxp_width (default 0.75 when unset)
        target_width = opt["bxp_width"] if opt["bxp_width"] else 0.75
        scale_factor = target_width / max(raw_widths) if raw_widths else 1.0
        widths = [w * scale_factor for w in raw_widths]
    else:
        widths = opt["bxp_width"]

    if opt.get("area_label"):
        areas_for_labels = [areas_dict.get(zid, 1.0) for zid in ordered_ids]
        if opt["area_label"] == "ha":
            area_labels = [
                (
                    "{:.1f} ha".format(a / 10000.0)
                    if a / 10000.0 < 10
                    else "{:.0f} ha".format(a / 10000.0)
                )
                for a in areas_for_labels
            ]
        elif opt["area_label"] == "km2":
            area_labels = [
                (
                    "{:.1f} km²".format(a / 1e6)
                    if a / 1e6 < 10
                    else "{:.0f} km²".format(a / 1e6)
                )
                for a in areas_for_labels
            ]
        elif opt["area_label"] == "acres":
            area_labels = [
                (
                    "{:.1f} ac".format(a / 4046.86)
                    if a / 4046.86 < 10
                    else "{:.0f} ac".format(a / 4046.86)
                )
                for a in areas_for_labels
            ]
        elif opt["area_label"] == "mi2":
            area_labels = [
                (
                    "{:.2f} mi²".format(a / 2.59e6)
                    if a / 2.59e6 < 10
                    else "{:.0f} mi²".format(a / 2.59e6)
                )
                for a in areas_for_labels
            ]
        else:
            area_labels = ["{:.0f} m²".format(a) for a in areas_for_labels]

    # Zonal colors need patch artists to receive their facecolor
    patch_artist = opt["bx_color"] is not None or bool(opt["bx_zonalcolors"])
    bxplot = ax.bxp(
        boxes, **build_bxp_kwargs(opt, widths=widths, patch_artist=patch_artist)
    )

    # Add area labels above each boxplot
    if opt.get("area_label"):
        label_fontsize = (opt["fontsize"] or plt.rcParams["font.size"]) * 0.85
        for i, label in enumerate(area_labels):
            if opt["vertical"]:
                ax.text(
                    i + 1,
                    ax.get_ylim()[1],
                    label,
                    ha="center",
                    va="bottom",
                    fontsize=label_fontsize,
                )
            else:
                ax.text(
                    ax.get_xlim()[1],
                    i + 1,
                    label,
                    va="center",
                    ha="left",
                    fontsize=label_fontsize,
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
    global mask_backup_name

    # lazy import matplotlib
    output = options["output"] if options["output"] else None
    lazy_import_py_modules(output)
    apply_style(options["style"])

    # Check if zonal map is an integer map
    if options["zones"]:
        check_integer(options["zones"])

    # Output options
    dpi, dimensions, vertical = get_output_options(
        options["dpi"], options["plot_dimensions"], flags["h"]
    )

    # boxplot parameters (unset appearance options -> None -> Matplotlib default)
    bxp_width = float(options["box_width"]) if options["box_width"] else None
    if bxp_width == 0:
        gs.fatal(_("The boxplot width needs to be larger than 0"))
    bx_color = get_valid_color(options["box_color"]) if options["box_color"] else None
    median_color = (
        get_valid_color(options["median_color"]) if options["median_color"] else None
    )

    # Whisker parameters
    whisker_range = float(options["range"])
    if whisker_range <= 0:
        gs.fatal(_("The range value need to be larger than 0"))

    # raster stats
    raster_stat_color = (
        get_valid_color(options["raster_stat_color"])
        if options["raster_stat_color"]
        else None
    )

    # Create new value rasters if there is a mask or the value raster
    # extent and resolution do not match that of the current region
    mask_present = checkmask()
    if bool(options["zones"]):
        valueraster_region = check_regionraster_match(options["map"])
        if mask_present or not valueraster_region:
            value_raster = create_temporary_name("tmpinput")
            Module(
                "r.mapcalc", expression="{} = {}".format(value_raster, options["map"])
            )
        else:
            value_raster = options["map"]
    else:
        value_raster = options["map"]

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

        # Temporarily disable the active mask by renaming the MASK raster.
        # mask_backup_name is set only after a successful rename so that
        # cleanup() does nothing if the rename itself failed (MASK still intact).
        if mask_present:
            backup_name = create_unique_name("maskbackup")
            Module("g.rename", raster=["MASK", backup_name])
            mask_backup_name = backup_name

    # Collect options
    base_options = {
        "value_name": options["map"],
        "value_raster": value_raster,
        "output": options["output"],
        "outliers": flags["o"],
        "notch": flags["n"],
        "name_outliers_map": options["map_outliers"],
        "fontsize": float(options["fontsize"]) if options["fontsize"] else None,
        "rotate_labels": options["rotate_labels"],
        "dimensions": dimensions,
        "dpi": dpi,
        "vertical": vertical,
        "bxp_linewidth": (
            float(options["box_linewidth"]) if options["box_linewidth"] else None
        ),
        "bxp_width": bxp_width,
        "bx_color": bx_color,
        "whisker_linewidth": (
            float(options["whisker_linewidth"])
            if options["whisker_linewidth"]
            else None
        ),
        "whisker_range": whisker_range,
        "flier_size": float(options["flier_size"]) if options["flier_size"] else None,
        "flier_marker": options["flier_marker"],
        "flier_color": (
            get_valid_color(options["flier_color"]) if options["flier_color"] else None
        ),
        "median_lw": (
            float(options["median_linewidth"]) if options["median_linewidth"] else None
        ),
        "median_color": median_color,
        "nprocs": int(options["nprocs"]),
    }
    if bool(options["zones"]):
        zone_options = {
            **base_options,
            **{
                "zones_name": options["zones"],
                "zones_raster": zonal_raster,
                "show_catnumbers": flags["s"],
                "bx_zonalcolors": flags["c"],
                "order": options["order"],
                "plot_rast_stats": options["raster_statistics"],
                "raster_stat_color": raster_stat_color,
                "raster_stat_alpha": float(options["raster_stat_alpha"]),
                "variable_box_width": options["box_width_variable"],
                "area_label": options["area_label"],
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

    # Restore the original mask after a successful run.
    # cleanup() handles restoration if the script exits with an error.
    if mask_present and bool(options["zones"]):
        restore_mask_backup()


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
