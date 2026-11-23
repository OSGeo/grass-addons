############################################################################
#
# MODULE:       t.rast.stl2ca (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Plotting for t.rast.stl2ca: the multi-panel STL figure drawn
#               for every category of a classification, each in its own
#               color, plus the vlines= parser.
#
#               Originally split out of t.rast.stl; t.rast.stl2ca keeps its
#               own copy since each GRASS addon is installed independently.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""Plotting (Matplotlib) for t.rast.stl2ca.

np/pd/mpl/plt are set by t.rast.stl2ca.lazy_import_py_modules() -- after GRASS
parses the command line -- rather than imported here, so a plain module scan
(--help, g.extension) never needs numpy/pandas/matplotlib installed.
"""

import os

import grass.script as gs

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by t.rast.stl2ca.lazy_import_py_modules() before any function below runs.
np = None
pd = None
mpl = None
plt = None


def apply_style(style):
    """Apply a Matplotlib style sheet: either a built-in style name, or the
    path to a custom .mplstyle file (e.g. to set 'axes.linewidth' thinner
    than any built-in style does).

    :param str style: name of a built-in Matplotlib style, or a path to a
        custom style file
    """
    if not style:
        return
    if style not in plt.style.available and not os.path.isfile(style):
        gs.fatal(
            _(
                "'{}' is neither a built-in style ({}) nor an existing "
                "file. A custom style is given as the path to a "
                ".mplstyle file."
            ).format(style, ", ".join(plt.style.available))
        )
    plt.style.use(style)


def parse_vlines(vlines_opt, labels_opt, temporal_type):
    """Parse the vlines/vlines_labels options into plot-ready positions.

    :param str vlines_opt: comma separated dates (absolute time) or integer
        time steps (relative time); may be empty
    :param str labels_opt: comma separated labels, in the same order and
        count as vlines_opt; may be empty (no labels)
    :param str temporal_type: 'absolute' or 'relative'
    :return list: list of (position, label|None) tuples, position being a
        pandas.Timestamp (absolute) or int (relative)
    """
    if not vlines_opt:
        return []
    raw_values = [v.strip() for v in vlines_opt.split(",") if v.strip()]
    positions = []
    for value in raw_values:
        if temporal_type == "relative":
            try:
                positions.append(int(value))
            except ValueError:
                gs.fatal(
                    _(
                        "Could not parse 'vlines' value '{}' as an integer time step."
                    ).format(value)
                )
        else:
            try:
                positions.append(pd.to_datetime(value))
            except (ValueError, TypeError):
                gs.fatal(
                    _("Could not parse 'vlines' value '{}' as a date.").format(value)
                )

    labels = [label.strip() for label in labels_opt.split(",")] if labels_opt else []
    if labels and len(labels) != len(positions):
        gs.fatal(
            _(
                "'vlines_labels' must have the same number of values as "
                "'vlines' ({labels} vs {vlines})."
            ).format(labels=len(labels), vlines=len(positions))
        )
    if not labels:
        labels = [None] * len(positions)
    return list(zip(positions, labels))


def category_colors(colormap, n):
    """Pick n distinct colors, one per category.

    Uses the colormap's own discrete entries when it has at least as many
    as there are categories (e.g. the qualitative 'tab10'/'tab20' palettes),
    so each category gets a clearly distinct color; falls back to sampling
    a continuous colormap ('viridis') evenly across its range once the
    category count exceeds what the chosen colormap offers.

    :param str colormap: name of a Matplotlib colormap (validated by the
        caller)
    :param int n: number of categories
    :return list: n Matplotlib colors
    """
    cmap = plt.get_cmap(colormap)
    if n <= cmap.N:
        return [cmap(i % cmap.N) for i in range(n)]
    gs.warning(
        _(
            "{n} categories exceed the {m} distinct colors '{c}' offers; "
            "falling back to the continuous 'viridis' colormap, which gives "
            "adjacent categories more similar colors."
        ).format(n=n, m=cmap.N, c=colormap)
    )
    fallback = plt.get_cmap("viridis")
    return [fallback(i / max(n - 1, 1)) for i in range(n)]


def draw_sen_line(ax, comp, trend_fit, trend_fit_segments, color):
    """Draw the Theil-Sen trend line(s) for one category, in its own color.

    No legend entry is added: the category is already named once in the
    figure's shared legend via its main series line, so the regression
    line (dashed, same color) is visually tied to it without repeating the
    label. Segmented (breakpoints=) or not, mirrors trend.decompose_and_fit's
    'trend_fit_segments' handling.

    :param ax: matplotlib Axes (the Trend panel)
    :param pandas.Series comp: the STL trend component for this category
    :param dict|None trend_fit: whole-series regression results from
        trend.fit_trend()
    :param list|None trend_fit_segments: per-segment (fit_trend() dict,
        label) pairs from trend.decompose_and_fit(), or None
    :param color: the category's line color
    """
    fits = (
        [seg_fit for seg_fit, _label in trend_fit_segments]
        if trend_fit_segments
        else ([trend_fit] if trend_fit is not None else [])
    )
    for fit in fits:
        if "sen_slope" not in fit:
            continue
        x0 = fit.get("x_start", 0)
        x1 = fit.get("x_stop", len(comp) - 1)
        x = np.arange(x0, x1 + 1)
        idx = comp.index[x0 : x1 + 1]
        sen = fit["sen_slope"] * x + fit["sen_intercept"]
        ax.plot(idx, sen, color=color, linestyle="--", linewidth=1, label="_nolegend_")


def plot_result(
    categories,
    output,
    dpi,
    dimensions,
    temporal_type="absolute",
    show_sen=False,
    show_band=False,
    line_width=None,
    fontsize=None,
    title=None,
    plots=None,
    colormap="tab10",
    vlines=None,
):
    """Build the multi-panel STL plot, in the style of R's plot(stl(...)),
    with one line per category drawn on each panel.

    Saves to file when output is given (format from extension), otherwise
    shows an interactive window.

    Every category gets its own color (see ``colormap``), shares the
    dispersion band / seasonal envelope / Theil-Sen trend line, and gets one
    legend for the whole figure (not per panel), placed below the bottom
    panel so it never overlaps a line.

    :param list categories: one dict per category, in plot/legend order,
        each with keys 'label' (str), 'result' (the STL fit: .observed,
        .trend, .seasonal, .resid), 'trend_fit' (trend.fit_trend() dict or
        None), 'trend_fit_segments' (list or None, see
        trend.decompose_and_fit()), 'band_lower'/'band_upper' (dispersion
        band Series or None), 'envelope_lower'/'envelope_upper' (seasonal
        envelope Series or None)
    :param str|None output: output image path, or None to show interactively
    :param float dpi: output resolution
    :param list dimensions: [width, height] in inches
    :param str temporal_type: 'absolute' or 'relative'
    :param bool show_sen: draw the Theil-Sen trend line on the Trend panel
    :param bool show_band: shade the dispersion band on the Observed panel
        (the band itself is per-category data, already computed by the
        caller -- this just toggles drawing it)
    :param line_width: series line width. Defaults to the Matplotlib default.
    :param fontsize: base font size. Defaults to the Matplotlib/style default.
    :param str|None title: the plot title. Empty/None draws no title.
    :param list|None plots: which panels to draw, as a subset of 'observed',
        'trend', 'seasonal' and 'residual'. None (or all four) draws the
        full four-panel figure.
    :param str colormap: Matplotlib colormap name
    :param list|None vlines: (position, label|None) pairs, position being a
        pandas.Timestamp (absolute time) or int (relative time), drawn as a
        dashed vertical reference line on every panel.
    """
    if fontsize is not None:
        plt.rcParams["font.size"] = fontsize
    legend_fontsize = fontsize * 0.9 if fontsize is not None else "small"

    all_panels = [
        ("Observed", lambda c: c["result"].observed),
        ("Trend", lambda c: c["result"].trend),
        ("Seasonal", lambda c: c["result"].seasonal),
        ("Residual", lambda c: c["result"].resid),
    ]
    if plots:
        selected = {p.lower() for p in plots}
        panels = [p for p in all_panels if p[0].lower() in selected]
    else:
        panels = all_panels

    colors = category_colors(colormap, len(categories))

    # squeeze=False keeps 'axes' 2-D so a single-panel figure indexes the same
    # way as a multi-panel one.
    fig, axes = plt.subplots(
        len(panels), 1, figsize=dimensions, sharex=True, squeeze=False
    )
    axes = axes[:, 0]

    for ax, (label, get_comp) in zip(axes, panels):
        ax.grid(axis="both", color="lightgrey", linewidth=0.3, zorder=0)

        for index, category in enumerate(categories):
            comp = get_comp(category)
            color = colors[index]

            if label == "Observed" and show_band:
                band_lower = category.get("band_lower")
                band_upper = category.get("band_upper")
                if band_lower is not None and band_upper is not None:
                    ax.fill_between(
                        comp.index,
                        band_lower.values,
                        band_upper.values,
                        color=color,
                        alpha=0.15,
                        linewidth=0,
                        zorder=1,
                        label="_nolegend_",
                    )

            if (
                label == "Seasonal"
                and category.get("envelope_lower") is not None
                and category.get("envelope_upper") is not None
            ):
                ax.plot(
                    comp.index,
                    category["envelope_upper"].values,
                    linestyle=":",
                    linewidth=1,
                    color=color,
                    alpha=0.8,
                    label="_nolegend_",
                )
                ax.plot(
                    comp.index,
                    category["envelope_lower"].values,
                    linestyle=":",
                    linewidth=1,
                    color=color,
                    alpha=0.8,
                    label="_nolegend_",
                )

            if label == "Residual":
                ax.plot(
                    comp.index,
                    comp.values,
                    marker="o",
                    markersize=2,
                    linestyle="none",
                    color=color,
                    label="_nolegend_",
                )
            else:
                ax.plot(
                    comp.index,
                    comp.values,
                    linewidth=line_width,
                    color=color,
                    label="_nolegend_",
                )

            if label == "Trend" and show_sen:
                draw_sen_line(
                    ax,
                    comp,
                    category.get("trend_fit"),
                    category.get("trend_fit_segments"),
                    color,
                )

        if label == "Residual":
            ax.axhline(0, color="grey", linewidth=0.8, zorder=1)

        ax.set_ylabel(label)
        ax.margins(x=0.01)

    handles = [
        mpl.lines.Line2D([], [], color=colors[i], linewidth=2, label=category["label"])
        for i, category in enumerate(categories)
    ]
    ncol = min(len(handles), 6) or 1
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=ncol,
        fontsize=legend_fontsize,
        frameon=False,
    )

    if vlines:
        for position, vline_label in vlines:
            for ax in axes:
                ax.axvline(
                    position,
                    color="black",
                    linestyle="--",
                    linewidth=0.8,
                    alpha=0.6,
                    zorder=2,
                )
            if vline_label:
                axes[0].annotate(
                    vline_label,
                    xy=(position, 1.0),
                    xycoords=("data", "axes fraction"),
                    xytext=(0, 3),
                    textcoords="offset points",
                    rotation=90,
                    va="bottom",
                    ha="center",
                    fontsize=legend_fontsize,
                )

    axes[-1].set_xlabel("Time step" if temporal_type == "relative" else "Date")
    fig.align_ylabels(axes)

    if title:
        fig.suptitle(title)

    # The shared legend is drawn outside the axes, below the bottom panel;
    # reserve space for it so tight_layout doesn't shrink it back under the
    # last panel.
    rect = (0, 0.08, 1, 1)

    if output:
        fig.tight_layout(rect=rect)
        fig.savefig(output, bbox_inches="tight", dpi=dpi)
        plt.close(fig)
        path_name = os.path.split(output)
        gs.message(
            _("Done, you can find the file {name} in {path}").format(
                name=path_name[1], path=path_name[0] or "."
            )
        )
    else:
        gs.message(_("Close the figure window to continue."))
        fig.tight_layout(rect=rect)
        plt.show()
        plt.close(fig)
