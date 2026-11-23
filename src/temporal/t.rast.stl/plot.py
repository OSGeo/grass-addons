############################################################################
#
# MODULE:       t.rast.stl (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Plotting for t.rast.stl: the multi-panel STL figure, trend
#               regression lines, colour helpers and the vlines= option
#               parser.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""Plotting (Matplotlib) for t.rast.stl.

np/pd/mpl/plt are set by t.rast.stl.lazy_import_py_modules() -- after GRASS
parses the command line -- rather than imported here, so a plain module scan
(--help, g.extension) never needs numpy/pandas/matplotlib installed.
"""

import colorsys
import os

import grass.script as gs

from trend import format_slope

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by t.rast.stl.lazy_import_py_modules() before any function below runs.
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
                        "Could not parse 'vlines' value '{}' as an integer "
                        "time step."
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


def grass_color_to_mpl(value):
    """Convert a colour spec to a matplotlib-usable colour.

    Accepts a broad range of notations: a GRASS ``R:G:B`` triplet with each
    component in 0-255 (rescaled to a 0-1 RGB tuple), or anything matplotlib
    already understands. The colon-separated form is only treated
    as an RGB triplet when its components are numeric, so colon-bearing
    matplotlib names such as ``tab:blue`` still pass straight through.

    :param str|None value: the option value (may be empty/None)
    :return: a matplotlib colour (str name or 0-1 RGB tuple), or None if unset
        or 'none'
    :raises ValueError: if an R:G:B triplet has out-of-range components
    """
    if not value:
        return None
    value = value.strip()
    # 'none' (allowed by G_OPT_CN) means no explicit colour here: fall back to
    # the default series colour rather than drawing an invisible line.
    if value.lower() == "none":
        return None
    # GRASS R:G:B[:A] triplet -- only when the parts are all numeric, so
    # colon-bearing matplotlib names (e.g. 'tab:blue') are left for matplotlib.
    if ":" in value:
        parts = value.split(":")
        if all(p.strip().lstrip("-").isdigit() for p in parts):
            if len(parts) not in (3, 4):
                raise ValueError("expected R:G:B or R:G:B:A")
            comps = []
            for p in parts:
                c = int(p)
                if not 0 <= c <= 255:
                    raise ValueError("each component must be in 0-255")
                comps.append(c / 255.0)
            return tuple(comps)
    # Otherwise hand back as-is for matplotlib to resolve (name or hex).
    return value


def trend_color_family(base_color):
    """Derive a 3-shade colour family (ols/sen/gam) from a base series colour.

    The regression lines for a dataset share the hue of its series but are
    shaded darker so they stand out against it: OLS darkest, Theil-Sen mid,
    GAM lightest (still darker than the series line). Returns a dict with
    'ols', 'sen' and 'gam' hex colours.

    :param str base_color: any matplotlib colour spec (name or hex)
    :return dict: {'ols': hex, 'sen': hex, 'gam': hex}
    """
    r, g, b = mpl.colors.to_rgb(base_color)
    h, light, s = colorsys.rgb_to_hls(r, g, b)
    # Boost saturation a touch and pick three lightness levels below the base.
    s = min(1.0, s + 0.1)

    def shade(lightness):
        rr, gg, bb = colorsys.hls_to_rgb(h, max(0.0, min(1.0, lightness)), s)
        return mpl.colors.to_hex((rr, gg, bb))

    return {
        "ols": shade(light * 0.45),
        "sen": shade(light * 0.7),
        "gam": shade(light * 0.9),
    }


def lighten_color(base_color, amount=0.55):
    """Lighten a colour toward white, for markers meant to recede from the
    main series line (excluded/outlier points: same hue, but visibly not
    part of the plotted line).

    :param str base_color: any matplotlib colour spec (name or hex)
    :param float amount: fraction (0-1) of the way from the base colour's
        lightness to white
    :return str: hex colour
    """
    r, g, b = mpl.colors.to_rgb(base_color)
    h, light, s = colorsys.rgb_to_hls(r, g, b)
    light = light + (1 - light) * amount
    rr, gg, bb = colorsys.hls_to_rgb(h, min(1.0, light), s)
    return mpl.colors.to_hex((rr, gg, bb))


def draw_trend_lines(
    ax,
    comp,
    trend_fit,
    show_ols,
    show_sen,
    show_gam,
    show_band,
    with_stats=True,
    colors=None,
    label_suffix="",
):
    """Draw the requested trend regression line(s) on a Trend panel axis.

    Each regression type has a fixed linestyle (OLS dashed, Theil-Sen
    dash-dot, GAM dotted). Colours are taken from ``colors``; passing a single
    colour (the dataset's family) for all three lets linestyle distinguish the
    regression type while colour distinguishes the dataset.

    :param ax: matplotlib Axes (the Trend panel, or its twin)
    :param pandas.Series comp: the STL trend component for this dataset
    :param dict trend_fit: regression results from fit_trend()
    :param bool show_ols: draw the OLS line
    :param bool show_sen: draw the Theil-Sen line
    :param bool show_gam: draw the monotone GAM curve
    :param bool show_band: shade the GAM 95% confidence band
    :param bool with_stats: include slope/R^2/p in the legend labels. Dropped
        when two datasets are plotted (the stats still print to the terminal).
    :param dict|None colors: per-line colours with keys 'ols', 'sen', 'gam'.
        Defaults to the single-dataset red/green/purple scheme.
    :param str label_suffix: appended to each legend label, e.g. " (precip)"
    :return list: the line handles drawn (for building a combined legend)
    """
    if colors is None:
        colors = {"ols": "tab:red", "sen": "tab:green", "gam": "tab:purple"}
    handles = []
    x0 = trend_fit.get("x_start", 0)
    x1 = trend_fit.get("x_stop", len(comp) - 1)
    x = np.arange(x0, x1 + 1)
    idx = comp.index[x0 : x1 + 1]

    if show_ols:
        ols = trend_fit["slope"] * x + trend_fit["intercept"]
        if with_stats:
            lbl = "OLS (slope = {}, $R^2$ = {:.3f}){}".format(
                format_slope(
                    trend_fit.get("slope_report", trend_fit["slope"]),
                    trend_fit.get("unit_label"),
                ),
                trend_fit["r2"],
                label_suffix,
            )
        else:
            lbl = "OLS" + label_suffix
        (h,) = ax.plot(
            idx, ols, color=colors["ols"], linestyle="--", linewidth=1, label=lbl
        )
        handles.append(h)
    if show_sen and "sen_slope" in trend_fit:
        sen = trend_fit["sen_slope"] * x + trend_fit["sen_intercept"]
        if with_stats:
            lbl = "Theil-Sen (slope = {}, MK p = {:.3f}){}".format(
                format_slope(
                    trend_fit.get("sen_slope_report", trend_fit["sen_slope"]),
                    trend_fit.get("unit_label"),
                ),
                trend_fit["mk_pvalue"],
                label_suffix,
            )
        else:
            lbl = "Theil-Sen" + label_suffix
        (h,) = ax.plot(
            idx, sen, color=colors["sen"], linestyle="-.", linewidth=1, label=lbl
        )
        handles.append(h)
    gam = trend_fit.get("gam") if show_gam else None
    if gam is not None:
        gidx = comp.index[gam["x"]]
        if show_band and gam.get("lower") is not None:
            ax.fill_between(
                gidx,
                gam["lower"],
                gam["upper"],
                color=colors["gam"],
                alpha=0.15,
                linewidth=0,
                zorder=1,
            )
        if with_stats:
            lbl = "Monotone GAM ({}, change = {}){}".format(
                gam["direction"], format_slope(gam["change"]), label_suffix
            )
        else:
            lbl = "Monotone GAM" + label_suffix
        (h,) = ax.plot(
            gidx,
            gam["fitted"],
            color=colors["gam"],
            linestyle=":",
            linewidth=1.5,
            label=lbl,
        )
        handles.append(h)
    return handles


def draw_trend_lines_for_dataset(
    ax,
    comp,
    trend_fit,
    trend_fit_segments,
    show_ols,
    show_sen,
    show_gam,
    show_band,
    with_stats,
    colors,
    dataset_suffix,
):
    """Draw one dataset's trend regression line(s), segmented or not.

    With ``trend_fit_segments`` (the breakpoints= option), the OLS/Theil-Sen
    lines are drawn once per segment, each labelled with its own date/step
    range; the monotone GAM curve, if requested, is still drawn once from
    ``trend_fit``, since it is always fit on the whole series regardless of
    breakpoints_opt. Without ``trend_fit_segments`` this is a plain,
    unsegmented call to draw_trend_lines() for ``trend_fit``, same as before
    the breakpoints= option existed.

    :param ax: matplotlib Axes (the Trend panel, or its twin)
    :param pandas.Series comp: the STL trend component for this dataset
    :param dict|None trend_fit: whole-series regression results from
        fit_trend()
    :param list|None trend_fit_segments: per-segment (fit_trend() dict,
        label) pairs from decompose_and_fit(), or None
    :param bool show_ols: draw the OLS line(s)
    :param bool show_sen: draw the Theil-Sen line(s)
    :param bool show_gam: draw the monotone GAM curve
    :param bool show_band: shade the GAM 95% confidence band (with show_gam)
    :param bool with_stats: include slope/R^2/p in the legend labels
    :param dict|None colors: per-line colours, see draw_trend_lines()
    :param str dataset_suffix: appended to every label, e.g. " (precip)" in
        two-dataset mode, else ""
    :return list: the line handles drawn (for building a combined legend)
    """
    if not trend_fit_segments:
        if trend_fit is None:
            return []
        return draw_trend_lines(
            ax,
            comp,
            trend_fit,
            show_ols,
            show_sen,
            show_gam,
            show_band,
            with_stats=with_stats,
            colors=colors,
            label_suffix=dataset_suffix,
        )

    handles = []
    for seg_fit, seg_label in trend_fit_segments:
        handles += draw_trend_lines(
            ax,
            comp,
            seg_fit,
            show_ols,
            show_sen,
            False,
            False,
            with_stats=with_stats,
            colors=colors,
            label_suffix=seg_label + dataset_suffix,
        )
    if show_gam and trend_fit is not None:
        handles += draw_trend_lines(
            ax,
            comp,
            trend_fit,
            False,
            False,
            True,
            show_band,
            with_stats=with_stats,
            colors=colors,
            label_suffix=dataset_suffix,
        )
    return handles


def plot_result(
    result,
    output,
    dpi,
    dimensions,
    east,
    north,
    temporal_type="absolute",
    trend_fit=None,
    trend_fit_segments=None,
    show_ols=True,
    show_sen=True,
    show_gam=False,
    show_band=False,
    show_stats=False,
    result2=None,
    trend_fit2=None,
    trend_fit_segments2=None,
    strds_name=None,
    strds2_name=None,
    same_yscale=False,
    line_color=None,
    line_color2=None,
    fontsize=None,
    line_width=None,
    title=None,
    plots=None,
    band_lower=None,
    band_upper=None,
    band_lower2=None,
    band_upper2=None,
    band_label=None,
    envelope_lower=None,
    envelope_upper=None,
    envelope_lower2=None,
    envelope_upper2=None,
    excluded=None,
    excluded2=None,
    vlines=None,
):
    """Build the multi-panel STL plot, in the style of R's plot(stl(...)).

    Saves to file when output is given (format from extension), otherwise
    shows an interactive window.

    When a second decomposition (``result2``) is given, both datasets are drawn
    on the same four panels. By default the second dataset is plotted on a twin
    right y-axis on each panel (its scale may differ); with ``same_yscale`` both
    datasets instead share one common y-axis range per panel (useful when the
    two are in comparable units). The two datasets are distinguished by colour,
    with a single legend (in the Observed panel) naming each. The per-dataset
    trend regression lines are drawn on the Trend panel for both; their
    slope/R^2/p statistics are omitted from the legend in the two-dataset case
    (they are still printed to the terminal) to keep the panel readable.

    :param bool show_ols: draw the ordinary least-squares (OLS) trend line.
    :param bool show_sen: draw the robust Theil-Sen trend line.
    :param bool show_gam: draw the monotone GAM trend curve.
    :param bool show_band: shade the GAM 95% confidence band (with show_gam).
    :param bool show_stats: include the trend-line statistics (slope, R^2,
        Mann-Kendall p, GAM net change) in the plot legend. When False, the
        legend just names each line; the statistics are always printed to the
        terminal regardless.
    :param list|None trend_fit_segments: per-segment (fit_trend() dict,
        label) pairs from decompose_and_fit()'s breakpoints_opt handling, or
        None. When given, these OLS/Theil-Sen lines are drawn instead of
        trend_fit's whole-series ones; trend_fit's GAM curve (if requested)
        is unaffected, since it is always fit on the whole series.
    :param object|None result2: STL fit of a second dataset to co-plot.
    :param dict|None trend_fit2: regressions for the second dataset.
    :param list|None trend_fit_segments2: same as trend_fit_segments, for
        the second dataset.
    :param str|None strds_name: name of the primary strds (legend).
    :param str|None strds2_name: name of the second strds (legend).
    :param bool same_yscale: share one common y-axis range between the two
        datasets on each panel instead of using a twin right axis.
    :param line_color: series line colour for the first dataset, as a
        matplotlib-ready colour (name or 0-1 RGB/RGBA tuple; the caller converts
        from GRASS colour syntax). Defaults to a blue.
    :param line_color2: series line colour for the second dataset. Defaults to
        an orange.
    :param list|None plots: which panels to draw, as a subset of 'observed',
        'trend', 'seasonal' and 'residual'. None (or all four) draws the full
        four-panel figure.
    :param pandas.Series|None band_lower: lower bound of the dispersion band
        for the primary dataset (zone mode with -d), aligned with
        ``result.observed``'s index. Shaded on the Observed panel only.
    :param pandas.Series|None band_upper: upper bound of that band.
    :param pandas.Series|None band_lower2: lower bound for the second
        dataset (when ``result2`` is given).
    :param pandas.Series|None band_upper2: upper bound for the second dataset.
    :param str|None band_label: legend label for the band (e.g. '± 1 SD' or
        'IQR (25-75%)').
    :param pandas.Series|None envelope_lower: rolling envelope lower bound of
        the primary dataset's seasonal component (the seasonal_envelope=
        option), aligned with ``result.seasonal``'s index. Drawn on the
        Seasonal panel only.
    :param pandas.Series|None envelope_upper: rolling envelope upper bound of
        that component.
    :param pandas.Series|None envelope_lower2: rolling envelope lower bound
        for the second dataset (when ``result2`` is given).
    :param pandas.Series|None envelope_upper2: rolling envelope upper bound
        for the second dataset.
    :param pandas.Series|None excluded: primary dataset's values dropped by
        the temporal_outliers= option (its own, irregular timestamps, not
        aligned with ``result.observed``). Drawn as markers on the Observed
        panel only, in a lighter shade of the series colour; excluded from
        the line itself, having already been interpolated over before STL
        ran.
    :param pandas.Series|None excluded2: same, for the second dataset.
    :param list|None vlines: (position, label|None) pairs, position being a
        pandas.Timestamp (absolute time) or int (relative time), drawn as a
        dashed vertical reference line on every panel.
    """
    have_second = result2 is not None
    # Series line colours: user-supplied or sensible defaults.
    color1 = line_color or "tab:blue"
    color2 = line_color2 or "tab:orange"
    # GRASS dataset names are "name@mapset"; show only the name in the legend.
    label1 = (strds_name or "strds").split("@")[0]
    label2 = (strds2_name or "strds2").split("@")[0]
    # Regression-line colour families, derived from each dataset's series colour
    # so custom colours propagate; linestyle then distinguishes OLS / Theil-Sen
    # / GAM within a dataset, while the colour family identifies the dataset.
    trend_colors1 = trend_color_family(color1)
    trend_colors2 = trend_color_family(color2)
    # Excluded-value markers: same hue as the series, but lightened so they
    # read as "not part of the line" rather than another data series.
    excluded_color1 = lighten_color(color1)
    excluded_color2 = lighten_color(color2)
    # A shared y-axis only makes sense with two datasets.
    shared_scale = have_second and same_yscale

    # Unset font size / line width fall back to the Matplotlib/style defaults.
    if fontsize is not None:
        plt.rcParams["font.size"] = fontsize
    legend_fontsize = fontsize * 0.9 if fontsize is not None else "small"
    all_panels = [
        ("Observed", result.observed, result2.observed if have_second else None),
        ("Trend", result.trend, result2.trend if have_second else None),
        ("Seasonal", result.seasonal, result2.seasonal if have_second else None),
        ("Residual", result.resid, result2.resid if have_second else None),
    ]
    # Keep only the requested panels, preserving the canonical top-to-bottom
    # order. An empty/None selection falls back to all four panels.
    if plots:
        selected = {p.lower() for p in plots}
        panels = [p for p in all_panels if p[0].lower() in selected]
    else:
        panels = all_panels
    # squeeze=False keeps 'axes' 2-D so a single-panel figure indexes the same
    # way as a multi-panel one.
    fig, axes = plt.subplots(
        len(panels), 1, figsize=dimensions, sharex=True, squeeze=False
    )
    axes = axes[:, 0]
    # Colour the primary series when a second dataset is present or the user
    # supplied a custom colour; otherwise keep matplotlib's default so a plain
    # single-dataset plot looks unchanged.
    primary_color = color1 if (have_second or line_color) else None
    # Twin axis of the Observed panel, if any, so the band patch drawn there
    # (see the 'have_second' block below) can be picked up for the combined
    # legend built after the loop.
    observed_twin_ax = None

    for ax, (label, comp, comp2) in zip(axes, panels):
        ax.grid(axis="both", color="lightgrey", linewidth=0.3, zorder=0)
        trend_handles = []

        # primary dataset on the left axis
        # ---------------------------------------------------------
        if label == "Observed" and band_lower is not None and band_upper is not None:
            ax.fill_between(
                comp.index,
                band_lower.values,
                band_upper.values,
                color=primary_color or "tab:blue",
                alpha=0.15,
                linewidth=0,
                zorder=1,
                label=band_label + (" ({})".format(label1) if have_second else ""),
            )
        if label == "Observed" and excluded is not None and len(excluded):
            ax.scatter(
                excluded.index,
                excluded.values,
                color=excluded_color1,
                s=16,
                zorder=3,
                label=_("Excluded outlier")
                + (" ({})".format(label1) if have_second else ""),
            )
        if label == "Observed" and not have_second:
            # Single-dataset: legend only appears when there's something to
            # name (the dispersion band and/or excluded-value markers); the
            # plain series line itself carries no label.
            if ax.get_legend_handles_labels()[0]:
                ax.legend(loc="best", fontsize=legend_fontsize, frameon=False)
        if (
            label == "Seasonal"
            and envelope_lower is not None
            and envelope_upper is not None
        ):
            env_color = primary_color or "tab:blue"
            ax.plot(
                comp.index,
                envelope_upper.values,
                linestyle="--",
                linewidth=1,
                color=env_color,
                alpha=0.8,
                label=_("Seasonal envelope")
                + (" ({})".format(label1) if have_second else ""),
            )
            ax.plot(
                comp.index,
                envelope_lower.values,
                linestyle="--",
                linewidth=1,
                color=env_color,
                alpha=0.8,
                label="_nolegend_",
            )
        if label == "Residual":
            ax.axhline(0, color="grey", linewidth=0.8, zorder=1)
            ax.plot(
                comp.index,
                comp.values,
                marker="o",
                markersize=2,
                linestyle="none",
                color=primary_color,
            )
        else:
            ax.plot(comp.index, comp.values, linewidth=line_width, color=primary_color)

        if label == "Trend" and trend_fit is not None:
            trend_handles += draw_trend_lines_for_dataset(
                ax,
                comp,
                trend_fit,
                trend_fit_segments,
                show_ols,
                show_sen,
                show_gam,
                show_band,
                with_stats=show_stats,
                colors=trend_colors1 if have_second else None,
                dataset_suffix=" ({})".format(label1) if have_second else "",
            )
            if not have_second:
                # Single-dataset: legend on the panel (stats or plain names).
                if ax.get_legend_handles_labels()[0]:
                    ax.legend(loc="best", fontsize=legend_fontsize, frameon=False)

        # Colour the left-axis ticks to match the first series only when the two
        # datasets sit on separate (twin) axes; with a shared scale the axis is
        # common to both, so its ticks stay neutral.
        if have_second and not shared_scale:
            ax.tick_params(axis="y", labelcolor=color1)

        # second dataset
        # ---------------------------------------------------------
        if have_second:
            # Shared scale: draw on the same axis. Twin scale: own right axis.
            ax2 = ax if shared_scale else ax.twinx()
            if label == "Observed":
                observed_twin_ax = ax2
            if (
                label == "Observed"
                and band_lower2 is not None
                and band_upper2 is not None
            ):
                ax2.fill_between(
                    comp2.index,
                    band_lower2.values,
                    band_upper2.values,
                    color=color2,
                    alpha=0.15,
                    linewidth=0,
                    zorder=1,
                    label=band_label + " ({})".format(label2),
                )
            if label == "Observed" and excluded2 is not None and len(excluded2):
                ax2.scatter(
                    excluded2.index,
                    excluded2.values,
                    color=excluded_color2,
                    s=16,
                    zorder=3,
                    label=_("Excluded outlier") + " ({})".format(label2),
                )
            if (
                label == "Seasonal"
                and envelope_lower2 is not None
                and envelope_upper2 is not None
            ):
                ax2.plot(
                    comp2.index,
                    envelope_upper2.values,
                    linestyle="--",
                    linewidth=1,
                    color=color2,
                    alpha=0.8,
                    label=_("Seasonal envelope") + " ({})".format(label2),
                )
                ax2.plot(
                    comp2.index,
                    envelope_lower2.values,
                    linestyle="--",
                    linewidth=1,
                    color=color2,
                    alpha=0.8,
                    label="_nolegend_",
                )
            if label == "Residual":
                if not shared_scale:
                    ax2.axhline(0, color="grey", linewidth=0.8, zorder=1)
                ax2.plot(
                    comp2.index,
                    comp2.values,
                    marker="o",
                    markersize=2,
                    linestyle="none",
                    color=color2,
                )
            else:
                ax2.plot(comp2.index, comp2.values, linewidth=line_width, color=color2)
            if not shared_scale:
                ax2.tick_params(axis="y", labelcolor=color2)
                ax2.margins(x=0.01)

            if label == "Trend" and trend_fit2 is not None:
                trend_handles += draw_trend_lines_for_dataset(
                    ax2,
                    comp2,
                    trend_fit2,
                    trend_fit_segments2,
                    show_ols,
                    show_sen,
                    show_gam,
                    show_band,
                    with_stats=show_stats,
                    colors=trend_colors2,
                    dataset_suffix=" ({})".format(label2),
                )

        if have_second and label == "Trend" and trend_handles:
            ax.legend(
                handles=trend_handles,
                loc="best",
                fontsize=legend_fontsize,
                frameon=False,
            )

        if label == "Seasonal" and (
            envelope_lower is not None or envelope_lower2 is not None
        ):
            handles, _env_labels = ax.get_legend_handles_labels()
            if have_second and not shared_scale:
                twin_handles, _env_twin_labels = ax2.get_legend_handles_labels()
                handles += twin_handles
            if handles:
                ax.legend(
                    handles=handles, loc="best", fontsize=legend_fontsize, frameon=False
                )

        ax.set_ylabel(label)
        ax.margins(x=0.01)

    # A single legend identifying the two datasets, on the Observed panel when
    # it is drawn, otherwise on the first panel. Any dispersion-band or
    # excluded-value handles drawn on that panel (via their own 'label=') are
    # picked up alongside.
    if have_second:
        observed_ax = next(
            (ax for ax, (label, *_) in zip(axes, panels) if label == "Observed"),
            axes[0],
        )
        line1 = mpl.lines.Line2D([], [], color=color1, linewidth=1, label=label1)
        line2 = mpl.lines.Line2D([], [], color=color2, linewidth=1, label=label2)
        band_handles, _band_labels = observed_ax.get_legend_handles_labels()
        if observed_twin_ax is not None and observed_twin_ax is not observed_ax:
            twin_handles, _twin_labels = observed_twin_ax.get_legend_handles_labels()
            band_handles += twin_handles
        observed_ax.legend(
            handles=[line1, line2] + band_handles,
            loc="best",
            fontsize=legend_fontsize,
            frameon=False,
        )

    # Vertical reference lines (vlines=), drawn on every panel; an optional
    # label per line is shown rotated just above the top panel only, to avoid
    # repeating it on each panel.
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

    # Plot title (empty means no title)
    if title:
        fig.suptitle(title)

    if output:
        fig.tight_layout()
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
        fig.tight_layout()
        plt.show()
        plt.close(fig)
