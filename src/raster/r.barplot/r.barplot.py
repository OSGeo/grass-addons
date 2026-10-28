#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.barplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws a barplot or piechart of a statistic (cell count,
#               surface area or a summary of a value raster) computed for
#               each category of a zonal raster layer.
#
# SPDX-FileCopyrightText: 2026 Paulo van Breugel
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
#
#############################################################################

# %module
# % description: Draws a barplot or piechart of a statistic per category of a zonal raster.
# % keyword: display
# % keyword: raster
# % keyword: plot
# % keyword: barplot
# % keyword: piechart
# % keyword: statistics
# %end

# %option G_OPT_R_MAP
# % key: zones
# % label: Zonal raster
# % description: Categorical (CELL) raster with the zones to summarize.
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_R_MAP
# % label: Value raster
# % description: Value raster to summarize per zone. Required for sum, mean, minimum and maximum.
# % required: no
# % guisection: Input
# %end

# %option
# % key: statistic
# % type: string
# % label: Statistic
# % description: Statistic to compute for each zone.
# % options: count,sum,mean,minimum,maximum
# % answer: count
# % required: yes
# % guisection: Input
# %end

# %option
# % key: unit
# % type: string
# % label: Unit (count only)
# % description: Reporting unit when statistic=count.
# % options: cells,percent,m2,ha,km2
# % answer: cells
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
# % description: Dimensions (width,height) of the figure in inches.
# % required: no
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Resolution of the plot in dots per inch.
# % required: no
# % guisection: Output
# %end

# %option
# % key: order
# % type: string
# % label: Sort order
# % description: Sort the bars/wedges by value.
# % options: ascending,descending
# % required: no
# % guisection: Plot format
# %end

# %flag
# % key: h
# % label: Horizontal barplot
# % description: Draw the bars horizontally (barplot only).
# % guisection: Plot format
# %end

# %flag
# % key: g
# % label: Add grid lines
# % description: Add grid lines (barplot only).
# % guisection: Plot format
# %end

# %flag
# % key: n
# % label: Show values
# % description: Print the value on top of each bar or in each pie wedge.
# % guisection: Plot format
# %end

# %option
# % key: rotate_labels
# % type: double
# % options: -90-90
# % label: Rotate labels (degrees)
# % description: Rotate the category labels (barplot only).
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: title
# % type: string
# % label: Plot title
# % description: Optional title above the plot.
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: y_label
# % type: string
# % label: Value axis label
# % description: Label of the value axis (barplot). Defaults to the statistic.
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: x_label
# % type: string
# % label: Category axis label
# % description: Label of the category axis (barplot).
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: fontsize
# % type: integer
# % label: Font size
# % description: Base font size.
# % answer: 10
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: title_fontsize
# % type: integer
# % label: Title font size
# % description: Font size of the title. Defaults to the base font size.
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: font
# % type: string
# % label: Font family
# % description: Font family for all text (e.g. sans-serif, serif, DejaVu Sans).
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: style
# % type: string
# % label: Matplotlib style
# % description: Matplotlib style sheet, see https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
# % required: no
# % guisection: Plot format
# % options: _mpl-gallery,_mpl-gallery-nogrid,bmh,classic,dark_background,fast,fivethirtyeight,ggplot,grayscale,seaborn-v0_8,seaborn-v0_8-bright,seaborn-v0_8-colorblind,seaborn-v0_8-dark,seaborn-v0_8-dark-palette,seaborn-v0_8-darkgrid,seaborn-v0_8-deep,seaborn-v0_8-muted,seaborn-v0_8-notebook,seaborn-v0_8-paper,seaborn-v0_8-pastel,seaborn-v0_8-poster,seaborn-v0_8-talk,seaborn-v0_8-ticks,seaborn-v0_8-white,seaborn-v0_8-whitegrid,Solarize_Light2,tableau-colorblind10
# %end

# %option
# % key: plot_type
# % type: string
# % label: Plot type
# % description: Draw a barplot or a piechart.
# % options: bar,pie
# % answer: bar
# % required: yes
# % guisection: Bar/pie format
# %end

# %option G_OPT_CN
# % key: color
# % label: Bar/wedge color
# % description: Fill color of the bars/wedges. Defaults to the style palette. See manual for color notation.
# % required: no
# % answer:
# % guisection: Bar/pie format
# %end

# %flag
# % key: c
# % label: Zonal colors
# % description: Fill bars/wedges with the colors of the zonal raster categories.
# % guisection: Bar/pie format
# %end

# %option G_OPT_C
# % key: border_color
# % label: Border color
# % description: Color of the bar/wedge borders. Defaults to the Matplotlib default.
# % answer:
# % required: no
# % guisection: Bar/pie format
# %end

# %option
# % key: border_width
# % type: double
# % label: Border width
# % description: Line width of the bar/wedge borders. Defaults to the Matplotlib default.
# % required: no
# % guisection: Bar/pie format
# %end

# %option G_OPT_M_NPROCS
# %end

import atexit
import os
import sys

import grass.script as gs

clean_layers = []


def create_temporary_name(prefix):
    """Create a temporary map name and register it for cleanup."""
    tmpf = gs.append_node_pid(prefix)
    clean_layers.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps."""
    mapset = gs.gisenv()["MAPSET"]
    for name in reversed(clean_layers):
        found = gs.find_file(name=name, element="raster", mapset=mapset)
        if found["file"]:
            gs.run_command("g.remove", flags="f", type="raster", name=name, quiet=True)


def lazy_import_py_modules(to_file):
    """Lazy import matplotlib, using a non-interactive backend when saving.

    :param bool to_file: True when the plot is written to an image file
    """
    global mpl
    global plt
    try:
        import matplotlib as mpl

        mpl.use("Agg" if to_file else "WXAgg")
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is not installed. Please, install it."))


def strip_mapset(name, join_char="@"):
    """Strip the mapset suffix from a map name."""
    return name.split(join_char)[0] if join_char in name else name


def check_map_exists(name):
    """Fail with a clean message if the raster map does not exist.

    :param str name: name of the raster map
    """
    if not gs.find_file(name=name, element="cell")["file"]:
        gs.fatal(_("Raster map <{}> not found").format(name))


def check_integer(name):
    """Ensure the zonal map is of type CELL, resolving reclass maps.

    :param str name: name of the zonal map

    :return str: name of a usable CELL raster (a temporary copy for reclass)
    """
    info = gs.raster_info(name)
    if info["datatype"] != "CELL":
        gs.fatal(_("The zonal raster must be of type CELL (integer)."))
    if info["maptype"] == "reclass":
        tmp_name = create_temporary_name("zonal_")
        gs.mapcalc(f"{tmp_name} = {name}", quiet=True)
        gs.run_command("r.colors", map=tmp_name, raster=name, quiet=True)
        gs.run_command("r.category", map=tmp_name, raster=name, quiet=True)
        return tmp_name
    return name


def get_valid_color(color):
    """Return a Matplotlib-compatible color from a GRASS color notation.

    :param str color: color as name, hex or R:G:B

    :return str|list: color usable by Matplotlib
    """
    if ":" in color:
        color = [int(x) / 255 for x in color.split(":")]
    if not mpl.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.").format(color))
    return color


def get_labels(zones):
    """Get the category ids and labels of the zonal map.

    :param str zones: name of the zonal map

    :return tuple: list of category ids and list of labels
    """
    cats = gs.read_command("r.category", map=zones, separator="pipe").splitlines()
    cats = [c for c in cats if c]
    ids = []
    labels = []
    for c in cats:
        parts = c.split("|")
        cid = int(parts[0])
        label = parts[1] if len(parts) > 1 and parts[1] else str(cid)
        ids.append(cid)
        labels.append(label)
    return ids, labels


def get_zonal_colors(zones, ids):
    """Get the color of each zonal category from its color table.

    :param str zones: name of the zonal map
    :param list ids: category ids to fetch colors for

    :return list: list of RGB colors aligned with ids
    """
    rows = gs.read_command(
        "r.what.color", input=zones, value=",".join(str(i) for i in ids)
    ).splitlines()
    lookup = {}
    for r in rows:
        cat, _sep, rgb = r.partition(":")
        rgb = rgb.strip()
        if rgb and rgb != "*":
            lookup[int(cat)] = get_valid_color(rgb)
    if not all(i in lookup for i in ids):
        gs.fatal(_("The zonal map does not have a color for every category."))
    return [lookup[i] for i in ids]


def univar_table(value, zones, nprocs):
    """Compute per-zone statistics of the value raster with r.univar.

    :param str value: name of the value raster
    :param str zones: name of the zonal raster
    :param int nprocs: number of threads for r.univar

    :return dict: {zone_id: {"count","sum","mean","minimum","maximum"}}
    """
    rows = gs.read_command(
        "r.univar", flags="t", map=value, zones=zones, separator="pipe", nprocs=nprocs
    ).splitlines()
    rows = [r for r in rows if r]
    header = rows[0].split("|")
    idx = {name: i for i, name in enumerate(header)}
    cols = {
        "count": idx["non_null_cells"],
        "sum": idx["sum"],
        "mean": idx["mean"],
        "minimum": idx["min"],
        "maximum": idx["max"],
    }
    izone = idx["zone"]
    table = {}
    for r in rows[1:]:
        f = r.split("|")
        table[int(f[izone])] = {k: float(f[i]) for k, i in cols.items()}
    return table


def count_table(zones):
    """Compute per-zone cell counts of the zonal raster with r.stats.

    :param str zones: name of the zonal raster

    :return dict: {zone_id: {"count": n}}
    """
    rows = gs.read_command(
        "r.stats", flags="cn", input=zones, separator="pipe"
    ).splitlines()
    table = {}
    for r in rows:
        if not r:
            continue
        cat, count = r.split("|")
        table[int(cat)] = {"count": float(count)}
    return table


def apply_unit(counts, unit):
    """Convert cell counts to the requested reporting unit.

    :param list counts: list of cell counts
    :param str unit: cells, percent, m2, ha or km2

    :return tuple: converted values and the axis label
    """
    if unit == "cells":
        return counts, "Cell count"
    if unit == "percent":
        total = sum(counts)
        vals = [100 * c / total if total else 0 for c in counts]
        return vals, "Percentage (%)"
    region = gs.region()
    cell_area = float(region["nsres"]) * float(region["ewres"])
    areas = [c * cell_area for c in counts]
    if unit == "m2":
        return areas, "Area (m²)"
    if unit == "ha":
        return [a / 1e4 for a in areas], "Area (ha)"
    return [a / 1e6 for a in areas], "Area (km²)"


def format_value(v, integer):
    """Format a value for display on the plot."""
    if integer:
        return f"{v:,.0f}"
    return f"{v:g}"


def main(options, flags):
    """Draw a barplot or piechart of a per-zone statistic."""

    output = options["output"]
    lazy_import_py_modules(bool(output))

    value = options["map"]
    statistic = options["statistic"]
    unit = options["unit"]
    plot_type = options["plot_type"]

    if statistic != "count" and not value:
        gs.fatal(_("Statistic '{}' requires a value raster (map=).").format(statistic))
    if statistic != "count" and unit != "cells":
        gs.warning(
            _("The unit option is ignored for statistic '{}'.").format(statistic)
        )
    if plot_type == "pie" and (options["x_label"] or options["y_label"]):
        gs.fatal(_("Axis labels do not apply to a piechart."))

    # Check the input maps exist before touching them.
    check_map_exists(options["zones"])
    if value:
        check_map_exists(value)

    # Resolve the zonal map (must be CELL, reclass maps are copied).
    zones = check_integer(options["zones"])
    ids, labels = get_labels(zones)

    nprocs = int(options["nprocs"])

    # Compute the statistic per zone.
    if statistic == "count":
        table = univar_table(value, zones, nprocs) if value else count_table(zones)
        counts = [table.get(i, {}).get("count", 0.0) for i in ids]
        values, default_label = apply_unit(counts, unit)
        integer_fmt = unit == "cells"
    else:
        table = univar_table(value, zones, nprocs)
        values = [table.get(i, {}).get(statistic, 0.0) for i in ids]
        default_label = "{} of {}".format(statistic.capitalize(), strip_mapset(value))
        integer_fmt = False

    axis_label = options["y_label"] if options["y_label"] else default_label

    # Colors. Fall back to the style/Matplotlib palette when neither the
    # zonal colors (-c) nor an explicit color are requested.
    if flags["c"]:
        colors = get_zonal_colors(zones, ids)
    elif options["color"]:
        colors = [get_valid_color(options["color"])] * len(ids)
    else:
        colors = None
    border_color = (
        get_valid_color(options["border_color"]) if options["border_color"] else None
    )
    border_width = float(options["border_width"]) if options["border_width"] else None

    # Only pass appearance kwargs that were set.
    edge_kwargs = {}
    if border_color is not None:
        edge_kwargs["edgecolor"] = border_color
    if border_width is not None:
        edge_kwargs["linewidth"] = border_width

    # Ordering.
    order = list(range(len(ids)))
    if options["order"] == "ascending":
        order = sorted(order, key=lambda i: values[i])
    elif options["order"] == "descending":
        order = sorted(order, key=lambda i: values[i], reverse=True)
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    if colors is not None:
        colors = [colors[i] for i in order]

    # Output options.
    dpi = float(options["dpi"]) if options["dpi"] else 300
    if options["plot_dimensions"]:
        dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    else:
        dimensions = [8, 4] if plot_type == "bar" and flags["h"] else [6, 6]

    # Style and fonts (user-defined fonts take precedence).
    if options["style"]:
        if options["style"] not in plt.style.available:
            gs.fatal(
                _("Unknown style '{}'. Available styles: {}").format(
                    options["style"], ", ".join(plt.style.available)
                )
            )
        plt.style.use(options["style"])
    plt.rcParams["font.size"] = int(options["fontsize"])
    if options["font"]:
        plt.rcParams["font.family"] = options["font"]
    title_fontsize = (
        int(options["title_fontsize"])
        if options["title_fontsize"]
        else int(options["fontsize"])
    )

    fig, ax = plt.subplots(figsize=dimensions)

    if plot_type == "pie":
        if any(v < 0 for v in values):
            gs.fatal(_("A piechart cannot be drawn with negative values."))
        autopct = (
            (lambda pct: format_value(pct * sum(values) / 100, integer_fmt))
            if flags["n"]
            else None
        )
        ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct=autopct,
            wedgeprops=edge_kwargs or None,
        )
        ax.set_aspect("equal")
    else:
        positions = range(len(values))
        bar_kwargs = dict(edge_kwargs)
        if colors is not None:
            bar_kwargs["color"] = colors
        if flags["h"]:
            bars = ax.barh(positions, values, **bar_kwargs)
            ax.set_yticks(list(positions))
            ax.set_yticklabels(labels)
            ax.set_xlabel(axis_label)
            if options["x_label"]:
                ax.set_ylabel(options["x_label"])
            ax.invert_yaxis()
        else:
            bars = ax.bar(positions, values, **bar_kwargs)
            ax.set_xticks(list(positions))
            ax.set_xticklabels(labels)
            ax.set_ylabel(axis_label)
            if options["x_label"]:
                ax.set_xlabel(options["x_label"])

        if flags["n"]:
            ax.bar_label(
                bars, labels=[format_value(v, integer_fmt) for v in values], padding=2
            )

        if flags["g"]:
            if flags["h"]:
                ax.xaxis.grid(True, alpha=0.5)
            else:
                ax.yaxis.grid(True, alpha=0.5)

        if options["rotate_labels"] and not flags["h"]:
            rotate = float(options["rotate_labels"])
            if abs(rotate) <= 10 or abs(rotate) >= 80:
                plt.xticks(rotation=rotate)
            elif rotate < 0:
                plt.xticks(rotation=rotate, ha="left", rotation_mode="anchor")
            else:
                plt.xticks(rotation=rotate, ha="right", rotation_mode="anchor")

    if options["title"]:
        ax.set_title(options["title"], fontsize=title_fontsize)

    if output:
        plt.savefig(output, bbox_inches="tight", dpi=dpi)
        plt.close()
        path = os.path.split(output)
        gs.message(
            _("File {name} written to {path}").format(name=path[1], path=path[0])
        )
    else:
        gs.message(_("\n> Close the figure window to finish the script.\n"))
        plt.tight_layout()
        plt.show()
        plt.close()


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
