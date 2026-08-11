#!/usr/bin/env python
############################################################################
#
# MODULE:       v.boxplot
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws the boxplot(s) of values in a vector attribute column
#
# COPYRIGHT:    (c) 2019-2026 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Draws a boxplot of values from a specified attribute column in a vector dataset, with an optional grouping based on categories in another column.
# % keyword: display
# % keyword: vector
# % keyword: plot
# % keyword: histogram
# % keyword: boxplot
# %end

# %option G_OPT_V_MAP
# % guisection: Input
# %end

# %option G_OPT_V_FIELD
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: column
# % description: Attribute column value to be plotted
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: group_by
# % description: Attribute column with categories to group the data by
# % required: no
# % guisection: Input
# %end

# %option G_OPT_DB_WHERE
# %guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# % label: Name of output image file
# % guisection: Output
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions
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
# % answer: 100
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
# % key: title
# % type: string
# % label: Plot title
# % description: The title of the plot. If left empty, no title is drawn.
# % required: no
# % guisection: Aesthetics
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
# % label: horizontal boxplot(s)
# % description: Draw the boxplot horizontal
# % guisection: Plot format
# %end

# %flag
# % key: n
# % label: notch
# % description: Draw boxplot(s) with notch
# % guisection: Plot format
# %end

# %flag
# % key: r
# % label: Rotate labels
# % description: rotate x-axis labels
# % guisection: Plot format
# %end

# %flag
# % key: g
# % label: Add grid lines
# % description: Add grid lines
# % guisection: Plot format
# %end

# %option
# % key: axis_limits
# % type: string
# % label: Limit value axis [min,max]
# % description: min and max value of y-axis, or x-axis if -h flag is set)
# % guisection: Plot format
# % required: no
# %end

# %option G_OPT_CN
# % key: box_color
# % label: Color of the boxplots
# % description: Fill color of the boxplots. Unset leaves the boxes unfilled (Matplotlib default).
# % required: no
# % answer:
# % guisection: Boxplot format
# %end

# %option G_OPT_CN
# % key: box_bordercolor
# % label: Color of the borders of the boxplots
# % description: Color of the borderlines of the boxplots. Defaults to the Matplotlib default.
# % required: no
# % answer:
# % guisection: Boxplot format
# %end

# %option
# % key: box_width
# % type: double
# % label: Boxplot width
# % description: The width of the boxplots (0,1]). Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
# % options: 0.1-1
# %end

# %option
# % key: box_linewidth
# % type: double
# % label: Boxplot line width
# % description: Width of the boxplot border lines. Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
# %end

# %option
# % key: whisker_linewidth
# % type: double
# % label: Whisker line width
# % description: Width of the whisker and cap lines. Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
# %end

# %option
# % key: median_linewidth
# % type: double
# % label: Median line width
# % description: width of the boxplot median line. Defaults to the Matplotlib default.
# % required: no
# % guisection: Boxplot format
# %end

# %option G_OPT_C
# % key: median_color
# % label: Color of the boxplot median line
# % description: Color of median. Defaults to the Matplotlib default.
# % required: no
# % answer:
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
# % type: double
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

# %flag
# % key: o
# % label: Include outliers
# % description: Draw boxplot(s) with outliers
# % guisection: Output
# %end

# %option G_OPT_V_OUTPUT
# % key: map_outliers
# % required: no
# % label: Vector map with the outliers
# % description: Create a vector map with the outlier features, classified by how many other groups they overlap with (n_overlap), on which side and how far they lie from their own group (side, iqr_dist), with matching colors in a GRASSRGB column.
# % guisection: Output
# %end

# %option
# % key: overlap_basis
# % type: string
# % label: Overlap basis
# % description: Range of the other groups an outlier is checked against to count overlaps: whisker (within the other group's whiskers/fences) or box (within its interquartile box)
# % required: no
# % options: whisker,box
# % answer: whisker
# % guisection: Output
# %end

import os
import json
import grass.script as gs
import numpy as np


def lazy_import_py_modules(backend):
    """Lazy import Py modules"""
    global mpl
    global plt

    # lazy import matplotlib
    try:
        import matplotlib as mpl

        if backend is None:
            mpl.use("WXAgg")
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


def get_valid_color(color):
    """Get valid Matplotlib color

    :param str color: input color

    :return str|list: color e.g. blue|[0.0, 0.0, 1.0]
    """
    if ":" in color:
        try:
            color = [int(x) / 255 for x in color.split(":")]
        except ValueError:
            gs.fatal(_("{} is not a valid color.").format(color))
    if not mpl.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.").format(color))
    return color


def build_where(user_where, column):
    """Build a WHERE clause that excludes NULL values in ``column``.

    The user clause is wrapped in parentheses so that its internal logic
    (e.g. ``a = 1 OR b = 2``) is preserved when combined with the
    ``IS NOT NULL`` condition.
    """
    if user_where:
        return "({}) AND {} IS NOT NULL".format(user_where, column)
    return "{} IS NOT NULL".format(column)


def read_records(vector, layer, columns, where):
    """Read attribute records as a list of dicts via v.db.select JSON output.

    JSON avoids the fragile parsing of pipe-separated output (group labels
    may contain a "|"), and returns already-typed values. Requires a GRASS
    version whose v.db.select supports format=json (GRASS >= 8.0).
    """
    txt = gs.read_command(
        "v.db.select",
        map_=vector,
        layer=layer,
        columns=",".join(columns),
        where=where,
        format="json",
    )
    return json.loads(txt)["records"]


def as_float(value, column):
    """Convert a value to float, failing cleanly with a GRASS message."""
    try:
        return float(value)
    except (TypeError, ValueError):
        gs.fatal(
            _("Column <{}> contains a non-numeric value: {}").format(column, value)
        )


def draw_boxplot(ax, data, horizontal, tick_labels=None, **kwargs):
    """Draw a boxplot, bridging Matplotlib keyword changes across versions.

    ``vert`` was superseded by ``orientation`` (boxplot: Matplotlib 3.10) and
    ``labels`` by ``tick_labels`` (Matplotlib 3.9). The correct keyword is
    chosen from the running Matplotlib version.
    """
    mpl_version = tuple(int(x) for x in mpl.__version__.split(".")[:2])
    if mpl_version >= (3, 10):
        kwargs["orientation"] = "horizontal" if horizontal else "vertical"
    else:
        kwargs["vert"] = not horizontal
    if tick_labels is not None:
        if mpl_version >= (3, 9):
            kwargs["tick_labels"] = tick_labels
        else:
            kwargs["labels"] = tick_labels
    return ax.boxplot(data, **kwargs)


def group_ranges(values, overlap_basis):
    """Compute the statistics of one group.

    Uses the same definition as Matplotlib's boxplot: Q1/Q3 via linear
    interpolation (np.percentile) and fences at Q1 - 1.5*IQR / Q3 + 1.5*IQR.

    :param values: 1D array of the group's values
    :param str overlap_basis: "whisker" or "box"

    :return tuple: (lower_fence, upper_fence, iqr, lo_overlap, hi_overlap),
        where [lo_overlap, hi_overlap] is the range used to decide whether a
        value from another group counts as overlapping this group.
    """
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    if overlap_basis == "box":
        lo_overlap, hi_overlap = q1, q3
    else:
        lo_overlap, hi_overlap = lower_fence, upper_fence
    return lower_fence, upper_fence, iqr, lo_overlap, hi_overlap


def classify_outliers(records, key_column, group_by, column, overlap_basis):
    """Classify the outliers of each group.

    :param records: list of dicts (from read_records) holding at least the key
        column, the value column, and the group column when group_by is set
    :param str key_column: name of the category (key) column
    :param str|None group_by: name of the grouping column, or None
    :param str column: name of the value column
    :param str overlap_basis: "whisker" or "box"

    :return dict: cat -> (side, iqr_dist, n_overlap) for outliers only, where
        side is "high"/"low" relative to the feature's own group, iqr_dist is
        the signed distance beyond its own group's fence in IQR units (+ above,
        - below; None when the group's IQR is 0 and the distance is undefined),
        and n_overlap is the number of *other* groups whose range (see
        overlap_basis) contains the value.
    """
    members = {}
    for row in records:
        grp = row[group_by] if group_by else ""
        members.setdefault(grp, []).append(
            (int(row[key_column]), as_float(row[column], column))
        )

    ranges = {
        grp: group_ranges(np.array([v for _, v in vals]), overlap_basis)
        for grp, vals in members.items()
    }

    classified = {}
    for grp, vals in members.items():
        lower_fence, upper_fence, iqr, _, _ = ranges[grp]
        for cat, val in vals:
            if val > upper_fence:
                side, ref = "high", upper_fence
            elif val < lower_fence:
                side, ref = "low", lower_fence
            else:
                continue
            iqr_dist = (val - ref) / iqr if iqr > 0 else None
            n_overlap = sum(
                lo <= val <= hi
                for other, (_, _, _, lo, hi) in ranges.items()
                if other != grp
            )
            classified[cat] = (side, iqr_dist, n_overlap)
    return classified


def outlier_rgb(side, n_overlap, max_overlap):
    """Derive a GRASSRGB string from the outlier classification.

    High outliers map onto a red ramp, low ones onto a blue ramp; the more
    isolated an outlier is (fewer overlaps), the darker/more saturated it is.
    The color is purely derived from n_overlap/side, so it can always be
    regenerated, e.g. with `v.colors ... column=n_overlap`.
    """
    frac = 0.0 if max_overlap <= 0 else n_overlap / max_overlap
    shade = 1.0 - 0.6 * frac  # isolated -> dark, widely shared -> lighter
    cmap = plt.get_cmap("Reds" if side == "high" else "Blues")
    r, g, b, _ = cmap(shade)
    return "{}:{}:{}".format(round(r * 255), round(g * 255), round(b * 255))


def write_map_outliers(
    records, vector, layer, column, group_by, key_column, overlap_basis, map_outliers
):
    """Create a vector map of the outliers with classification columns.

    ``records`` is the already-read attribute table (list of dicts) that was
    also used for plotting, so the exported outliers match the plotted ones.
    """
    has_group = bool(group_by)
    classified = classify_outliers(records, key_column, group_by, column, overlap_basis)
    if not classified:
        gs.warning(_("No outliers found. The outlier map is not created."))
        return

    max_overlap = max(n for _, _, n in classified.values())
    cats = sorted(classified)

    if not has_group:
        gs.warning(
            _(
                "No group_by column given; overlap between groups cannot be "
                "determined. The 'n_overlap' column is not created."
            )
        )

    gs.run_command(
        "v.extract",
        input=vector,
        layer=layer,
        output=map_outliers,
        cats=",".join(str(c) for c in cats),
        quiet=True,
    )

    try:
        out = gs.vector_db(map_outliers)[int(layer)]
    except KeyError:
        gs.fatal(
            _("No attribute table connected to layer {} of <{}>.").format(
                layer, map_outliers
            )
        )

    # Add only columns that do not already exist (the copied table may, for
    # instance, already contain a GRASSRGB column). Values are written with
    # UPDATE afterwards, overwriting any pre-existing content.
    wanted = [("side", "varchar(4)"), ("iqr_dist", "double precision")]
    if has_group:
        wanted.append(("n_overlap", "integer"))
    wanted.append(("GRASSRGB", "varchar(11)"))
    existing = {c.lower() for c in gs.vector_columns(map_outliers, layer)}
    to_add = [
        "{} {}".format(name, ctype)
        for name, ctype in wanted
        if name.lower() not in existing
    ]
    if to_add:
        gs.run_command(
            "v.db.addcolumn",
            map_=map_outliers,
            columns=",".join(to_add),
            quiet=True,
        )

    statements = []
    for cat in cats:
        side, iqr_dist, n_overlap = classified[cat]
        sets = "side='{}'".format(side)
        sets += ", iqr_dist={}".format(
            "NULL" if iqr_dist is None else "{:.6f}".format(iqr_dist)
        )
        if has_group:
            sets += ", n_overlap={}".format(n_overlap)
        sets += ", GRASSRGB='{}'".format(outlier_rgb(side, n_overlap, max_overlap))
        statements.append(
            "UPDATE {tbl} SET {sets} WHERE {key}={cat};".format(
                tbl=out["table"], sets=sets, key=out["key"], cat=cat
            )
        )
    if out["driver"] == "sqlite":  # wrap in one transaction for speed
        statements = ["BEGIN;"] + statements + ["COMMIT;"]

    sqlfile = gs.tempfile()
    with open(sqlfile, "w") as fh:
        fh.write("\n".join(statements) + "\n")
    gs.run_command("db.execute", input=sqlfile, quiet=True)
    try:
        os.remove(sqlfile)
    except OSError:
        pass

    gs.message(
        _("Outlier map <{}> created with {} outlier features.").format(
            map_outliers, len(cats)
        )
    )


def main():
    # lazy import matplotlib
    output = options["output"] if options["output"] else None
    lazy_import_py_modules(output)
    apply_style(options["style"])

    # input
    vector = options["map"]
    layer = options["layer"]
    column = options["column"]
    dpi = float(options["dpi"])
    grid = flags["g"]
    if options["plot_dimensions"]:
        dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
    else:
        if flags["h"]:
            dimensions = [6, 4]
        else:
            dimensions = [4, 6]
    # Appearance options; unset ones are omitted so Matplotlib/style defaults
    # apply. Without a fill color the boxes are drawn unfilled (patch_artist off).
    blcolor = (
        get_valid_color(options["box_bordercolor"])
        if options["box_bordercolor"]
        else None
    )
    bxcolor = get_valid_color(options["box_color"]) if options["box_color"] else None
    box_linewidth = (
        float(options["box_linewidth"]) if options["box_linewidth"] else None
    )
    whisker_linewidth = (
        float(options["whisker_linewidth"]) if options["whisker_linewidth"] else None
    )
    boxprops = {}
    if blcolor is not None:
        boxprops["color"] = blcolor
    if bxcolor is not None:
        boxprops["facecolor"] = bxcolor
    if box_linewidth is not None:
        boxprops["linewidth"] = box_linewidth
    median_color = (
        get_valid_color(options["median_color"]) if options["median_color"] else None
    )
    medianprops = {}
    if median_color is not None:
        medianprops["color"] = median_color
    if options["median_linewidth"]:
        medianprops["linewidth"] = float(options["median_linewidth"])
    lineprops = {}
    if whisker_linewidth is not None:
        lineprops["linewidth"] = whisker_linewidth
    if blcolor is not None:
        lineprops["color"] = blcolor
    whiskerprops = dict(lineprops)
    capprops = dict(lineprops)
    flier_color = (
        get_valid_color(options["flier_color"]) if options["flier_color"] else None
    )
    flierprops = {"marker": options["flier_marker"]}
    if options["flier_size"]:
        flierprops["markersize"] = float(options["flier_size"])
    if flier_color is not None:
        flierprops["markerfacecolor"] = flier_color
        flierprops["markeredgecolor"] = flier_color
    if box_linewidth is not None:
        flierprops["markeredgewidth"] = box_linewidth
    patch_artist = bxcolor is not None
    width_kwargs = (
        {"widths": float(options["box_width"])} if options["box_width"] else {}
    )
    group_by = options["group_by"] if options["group_by"] else None
    map_outliers = options["map_outliers"] if options["map_outliers"] else None
    overlap_basis = options["overlap_basis"] if options["overlap_basis"] else "whisker"
    where = build_where(options["where"], column)
    sort = options["order"] if options["order"] else None
    horizontal = flags["h"]
    flag_o = flags["o"]
    flag_n = flags["n"]
    flag_r = flags["r"]

    # The key column is only needed to identify features for the outlier map.
    if map_outliers:
        try:
            key_column = gs.vector_db(vector)[int(layer)]["key"]
        except KeyError:
            gs.fatal(
                _("No attribute table connected to layer {} of <{}>.").format(
                    layer, vector
                )
            )
    else:
        key_column = None

    # Read the data once (as typed JSON records) and reuse it for both the
    # plot and, if requested, the outlier map.
    sel_cols = list(filter(None, [key_column, group_by, column]))
    records = read_records(vector, layer, sel_cols, where)
    if not records:
        gs.fatal(_("No non-NULL values found for column <{}>.").format(column))

    # Set plot dimensions and fontsize
    if bool(options["fontsize"]):
        plt.rcParams["font.size"] = int(options["fontsize"])

    # Closing message
    if not options["output"]:
        gs.message(
            _("\n> Note, you need to close the figure to finish the script \n\n")
        )

    # Set plot dimensions and DPI
    fig, ax = plt.subplots(figsize=dimensions, dpi=dpi)

    # for grouped boxplot
    if group_by:
        # One pass: collect values per group in first-seen order
        grouped = {}
        for row in records:
            grouped.setdefault(row[group_by], []).append(as_float(row[column], column))
        items = list(grouped.items())

        # Order boxes by median (data and labels are sorted together, so no
        # position remapping is needed)
        if sort:
            items.sort(
                key=lambda kv: np.median(kv[1]),
                reverse=(sort == "descending"),
            )
        uid = [str(k) for k, _ in items]
        data = [v for _, v in items]

        # Draw boxplot
        draw_boxplot(
            ax,
            data,
            horizontal=horizontal,
            tick_labels=uid,
            notch=flag_n,
            showfliers=flag_o,
            boxprops=boxprops,
            medianprops=medianprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            flierprops=flierprops,
            patch_artist=patch_artist,
            **width_kwargs,
        )
    else:
        data = [as_float(row[column], column) for row in records]
        draw_boxplot(
            ax,
            data,
            horizontal=horizontal,
            notch=flag_n,
            showfliers=flag_o,
            boxprops=boxprops,
            medianprops=medianprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            flierprops=flierprops,
            patch_artist=patch_artist,
            **width_kwargs,
        )

    # Rotate the labels on the categorical (group) axis
    if flag_r:
        ax.tick_params(axis="y" if horizontal else "x", labelrotation=90)

    # Plot title (empty means no title)
    if options["title"]:
        ax.set_title(options["title"])

    plt.tight_layout()

    # Set limits value axis (the value axis is x when horizontal, else y)
    if bool(options["axis_limits"]):
        minlim, maxlim = map(float, options["axis_limits"].split(","))
        if horizontal:
            plt.xlim([minlim, maxlim])
        else:
            plt.ylim([minlim, maxlim])

    # Set grid (optional) on the value axis
    if horizontal:
        ax.xaxis.grid(bool(grid))
    else:
        ax.yaxis.grid(bool(grid))

    # Create the outlier map (optional)
    if map_outliers:
        write_map_outliers(
            records=records,
            vector=vector,
            layer=layer,
            column=column,
            group_by=group_by,
            key_column=key_column,
            overlap_basis=overlap_basis,
            map_outliers=map_outliers,
        )

    if output:
        plt.savefig(output)
    else:
        plt.show()


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
