############################################################################
#
# MODULE:       t.rast.stl2ca (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Interactive (Plotly) plotting for t.rast.stl2ca: the same
#               multi-panel STL figure as plot.py, exported as a
#               self-contained HTML page with legend-click category
#               highlighting, a hover crosshair synced across every panel,
#               and a trend-statistics sidebar.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""Interactive (Plotly) plotting for t.rast.stl2ca.

go/make_subplots are set by t.rast.stl2ca.lazy_import_plotly() -- called
only for the '-i' output mode -- rather than imported here, so a plain
module scan (--help, g.extension) or an ordinary Matplotlib run never need
Plotly installed.
"""

import os
import tempfile
import webbrowser
from html import escape as html_escape

import grass.script as gs

from plot import category_colors
from trend import trend_stats_rows

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by t.rast.stl2ca.lazy_import_plotly() before plot_interactive() runs.
go = None
make_subplots = None


# Three pieces of genuinely new logic, all operating on the same 'gd' plot
# div, kept in one script so later ones can reuse earlier lookups -- see the
# commit message/PR for a plain-language description of each, per AGENTS.md:
#
# 1. Category highlighting: cancels Plotly's default legend click (show/hide
#    that trace) and instead toggles the clicked category in a highlighted
#    set. With the set non-empty, every other category's traces are
#    restyled to a flat grey at reduced opacity, while the selected
#    categories keep their original color -- an empty set (nothing
#    selected, or toggled back off) restores everyone. Relies on each
#    trace's 'meta.category', set once when the trace is built (see
#    plot_interactive() below): one category's main line, dispersion band,
#    seasonal envelope and Theil-Sen line are all found and restyled
#    together regardless of which panel they are drawn in.
# 2. Full-viewport sizing: the page is sized to exactly the browser
#    window's height, and the chart is given all of it -- otherwise the
#    chart renders at a fixed, often much shorter height, leaving blank
#    space below it rather than using the space a maximized browser window
#    offers.
# 3. Hover crosshair: Plotly's own per-axis spike lines
#    (xaxis.showspikes/spikemode="across") were tried first, but only
#    extend within the one subplot being hovered -- not across the other
#    panels, which is the actual point of a crosshair on stacked panels
#    sharing a time axis. One thin vertical line shape is pre-added per
#    panel instead (see plot_interactive() below), hidden until the first
#    hover; plotly_hover moves every panel's line to the hovered date and
#    shows it, plotly_unhover hides them again.
#
# A fourth piece -- checkboxes to show/hide individual panels, each
# collapsing to hand its space to the rest -- was tried and then removed:
# panels kept rendering empty or disappearing in combinations beyond the
# ones tried while building it, and were not worth the trouble relative to
# just choosing 'plots=' before running. Picking which panels to draw is a
# plain Matplotlib-style 'plots' parameter again (see plot_interactive()).
_INTERACTIVITY_SCRIPT = """
(function () {
  var gd = document.getElementById('{plot_id}');

  // -- 1. Category highlighting on legend click -----------------------
  var selected = new Set();
  var original = gd.data.map(function (trace) {
    return {
      line: trace.line ? trace.line.color : undefined,
      marker: trace.marker ? trace.marker.color : undefined,
      fill: trace.fillcolor,
    };
  });
  var GREY = "#cfcfcf";
  var GREY_FILL = "rgba(207,207,207,0.15)";
  var DIM_OPACITY = 0.35;

  function restyleHighlight() {
    var lineColors = [];
    var markerColors = [];
    var fillColors = [];
    var opacities = [];
    for (var i = 0; i < gd.data.length; i++) {
      var dim = selected.size > 0 && !selected.has(gd.data[i].meta.category);
      lineColors.push(dim ? GREY : original[i].line);
      markerColors.push(dim ? GREY : original[i].marker);
      // Only the dispersion-band fill traces set fillcolor; restyling it on
      // every other trace too is a harmless no-op since they have no fill.
      fillColors.push(dim && original[i].fill ? GREY_FILL : original[i].fill);
      opacities.push(dim ? DIM_OPACITY : 1);
    }
    Plotly.restyle(gd, {
      "line.color": lineColors,
      "marker.color": markerColors,
      fillcolor: fillColors,
      opacity: opacities,
    });
  }

  gd.on("plotly_legendclick", function (clicked) {
    var category = gd.data[clicked.curveNumber].meta.category;
    if (selected.has(category)) {
      selected.delete(category);
    } else {
      selected.add(category);
    }
    restyleHighlight();
    return false;
  });

  // -- 2. Fill the browser window's full height -------------------------
  // Plotly's responsive config (see config={"responsive": True} in
  // plot_interactive()) resizes the chart to fill whatever height its
  // container is given; nothing gives it one beyond the default
  // content-sized page, so without this the chart renders at a fixed,
  // often much shorter height with blank space below it. The chart's own
  // margin.b (set in plot_interactive()) still reserves room for the
  // legend within that.
  document.documentElement.style.height = "100%";
  document.body.style.cssText = "height:100%; margin:0;";
  gd.style.height = "100vh";
  Plotly.Plots.resize(gd);

  // -- 3. Hover crosshair across every panel ----------------------------
  // plot_interactive() records exactly which fig.layout.shapes indices are
  // the crosshair lines (see meta.crosshairShapeIndices there): the figure
  // can contain other shapes too (the Residual zero-line, vlines=), so
  // their positions are not assumed, only looked up.
  var crosshairIndices = gd.layout.meta.crosshairShapeIndices;
  gd.on("plotly_hover", function (ev) {
    if (!ev.points || !ev.points.length) {
      return;
    }
    var x = ev.points[0].x;
    var update = {};
    crosshairIndices.forEach(function (i) {
      update["shapes[" + i + "].x0"] = x;
      update["shapes[" + i + "].x1"] = x;
      update["shapes[" + i + "].visible"] = true;
    });
    Plotly.relayout(gd, update);
  });
  gd.on("plotly_unhover", function () {
    var update = {};
    crosshairIndices.forEach(function (i) {
      update["shapes[" + i + "].visible"] = false;
    });
    Plotly.relayout(gd, update);
  });
})();
"""


def _rgba_string(color, alpha=1.0):
    """Convert a Matplotlib RGBA color (floats 0-1) to a Plotly color string.

    :param color: a Matplotlib color, e.g. from plot.category_colors()
    :param float alpha: opacity, 0-1
    """
    r, g, b = color[:3]
    return f"rgba({round(r * 255)},{round(g * 255)},{round(b * 255)},{alpha})"


def _sen_line_segments(comp, trend_fit, trend_fit_segments):
    """Compute the Theil-Sen trend line's x/y arrays for one category.

    Mirrors plot.draw_sen_line()'s segment handling (the whole-series fit,
    or one segment per 'breakpoints' split), but returns the data instead
    of drawing it onto a Matplotlib Axes, since this module builds Plotly
    traces instead.

    :param pandas.Series comp: the STL trend component for this category
    :param dict|None trend_fit: see plot.draw_sen_line()
    :param list|None trend_fit_segments: see plot.draw_sen_line()
    :return list: (x_values, y_values) pairs, one per segment with a
        computable Sen slope
    """
    fits = (
        [seg_fit for seg_fit, _label in trend_fit_segments]
        if trend_fit_segments
        else ([trend_fit] if trend_fit is not None else [])
    )
    segments = []
    for fit in fits:
        if "sen_slope" not in fit:
            continue
        x0 = fit.get("x_start", 0)
        x1 = fit.get("x_stop", len(comp) - 1)
        idx = comp.index[x0 : x1 + 1]
        sen = [fit["sen_slope"] * xi + fit["sen_intercept"] for xi in range(x0, x1 + 1)]
        segments.append((idx, sen))
    return segments


# (row dict key, column header) pairs, in display order -- matches
# trend.trend_stats_rows()'s own keys (shared with the stats_output= CSV,
# see trend.write_trend_stats_csv()).
_STATS_TABLE_COLUMNS = [
    ("category", "Category"),
    ("segment", "Segment"),
    ("n_obs", "N obs"),
    ("unit", "Unit"),
    ("sen_slope", "Sen slope"),
    ("mk_tau", "MK tau"),
    ("mk_pvalue", "MK p"),
]


def _format_stat_cell(value):
    """Format one trend_stats_rows() value for the HTML stats table.

    :param value: a cell value -- float, int, str or None
    """
    if isinstance(value, float):
        return f"{value:.4g}"
    if value is None:
        return ""
    return html_escape(str(value))


def _stats_sidebar_html(categories):
    """Build a sidebar panel with the same trend statistics as
    stats_output= (see trend.trend_stats_rows()), as plain HTML/CSS -- the
    open/close itself is the "checkbox hack" (a hidden checkbox, toggled by
    a <label>, with a CSS sibling selector reacting to it while it is
    checked), so no JavaScript is needed. A fixed tab in the top-left
    corner (chosen to stay clear of Plotly's own modebar icons, top-right
    of the chart) opens and closes it; a second label inside the panel,
    for the same checkbox, acts as its close button.

    Opening the panel *pushes the chart aside* rather than overlaying it,
    by wrapping the chart (the HTML plot_interactive() built above, spliced
    in as-is) and the panel together in one flex row: the chart area is
    flex:1 (takes whatever space the panel doesn't) and the panel's own
    width is 0/collapsed unless the checkbox is checked. This needs no
    extra JavaScript either: Plotly's own responsive handling (see
    config={{"responsive": True}} in plot_interactive()) already redraws
    the chart to fit its container whenever that container's size changes,
    which a CSS flex-width transition does exactly as well as a real
    window resize would.

    :param list categories: see plot.plot_result()
    :return tuple: (prefix, suffix) HTML to splice into the page right
        after '<body>' and right before '</body>' respectively (opening
        and closing the flex row around the chart), or ('', '') if there
        are no trend statistics to show (mirrors write_trend_stats_csv()'s
        own "nothing to write" case) -- then the chart is left alone,
        full-page, with no wrapper and nothing to push it aside.
    """
    rows = trend_stats_rows(categories)
    if not rows:
        return "", ""

    header_cells = "".join(f"<th>{label}</th>" for _key, label in _STATS_TABLE_COLUMNS)
    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{_format_stat_cell(row.get(key))}</td>"
            for key, _label in _STATS_TABLE_COLUMNS
        )
        body_rows.append(f"<tr>{cells}</tr>")

    style = """
<style>
  .stl2ca-stats-table { border-collapse: collapse; font-size: 13px; }
  .stl2ca-stats-table th, .stl2ca-stats-table td {
    border: 1px solid #ddd; padding: 4px 10px; text-align: right;
  }
  .stl2ca-stats-table th { background: #f3f3f3; }
  .stl2ca-stats-table td:first-child, .stl2ca-stats-table th:first-child {
    text-align: left;
  }
  #stl2ca-stats-toggle { display: none; }
  .stl2ca-stats-tab {
    position: fixed; top: 12px; left: 12px; z-index: 1000;
    font-family: sans-serif; font-size: 13px; cursor: pointer;
    background: #fff; border: 1px solid #ccc; border-radius: 4px;
    padding: 6px 12px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
    user-select: none;
  }
  .stl2ca-layout { display: flex; height: 100vh; }
  .stl2ca-chart-area { flex: 1; min-width: 0; }
  .stl2ca-stats-panel {
    width: 0; overflow: hidden; height: 100vh; box-sizing: border-box;
    background: #fff; box-shadow: -2px 0 10px rgba(0, 0, 0, 0.2);
    transition: width 0.25s ease; position: relative;
  }
  #stl2ca-stats-toggle:checked ~ .stl2ca-layout .stl2ca-stats-panel {
    width: 650px; max-width: 95vw;
  }
  .stl2ca-stats-panel > div { padding: 50px 16px 16px; font-family: sans-serif; }
  .stl2ca-stats-close {
    position: absolute; top: 12px; right: 16px; cursor: pointer;
    font-size: 18px; color: #888;
  }
</style>
"""
    prefix = (
        style
        + '<input type="checkbox" id="stl2ca-stats-toggle">'
        + '<label for="stl2ca-stats-toggle" class="stl2ca-stats-tab">'
        + "Trend statistics</label>"
        + '<div class="stl2ca-layout"><div class="stl2ca-chart-area">'
    )
    suffix = f"""
</div><div class="stl2ca-stats-panel"><div>
  <label for="stl2ca-stats-toggle" class="stl2ca-stats-close">&times;</label>
  <div style="overflow-x: auto;">
    <table class="stl2ca-stats-table">
      <thead><tr>{header_cells}</tr></thead>
      <tbody>{"".join(body_rows)}</tbody>
    </table>
  </div>
</div></div></div>
"""
    return prefix, suffix


def plot_interactive(
    categories,
    output,
    temporal_type="absolute",
    plots=None,
    colormap="tab10",
    title=None,
    line_width=None,
    fontsize=None,
    show_sen=False,
    show_band=False,
    vlines=None,
):
    """Build the same multi-panel STL figure as plot.plot_result(), as a
    self-contained interactive HTML page instead of a static image.

    Every category gets the same color as the static figure (via
    plot.category_colors()) and one shared legend entry. Clicking a
    legend entry highlights that category across every panel and fades
    the rest to grey; hovering any panel draws a crosshair through every
    panel at that date (see _INTERACTIVITY_SCRIPT above for both). A
    "Trend statistics" tab in the top-left corner opens a sidebar, pushing
    the chart aside, holding the same table as stats_output= (see
    _stats_sidebar_html() above), whether or not stats_output= is actually
    given -- it costs nothing extra to show, since trend_fit is already
    computed either way. Saves to 'output' when given (must end in '.html'),
    otherwise opens in a browser tab.

    :param list categories: see plot.plot_result()
    :param str|None output: output .html path, or None to open in a browser
    :param str temporal_type: 'absolute' or 'relative'
    :param list|None plots: which panels to draw (see plot.plot_result())
    :param str colormap: Matplotlib colormap name (reused for the colors)
    :param str|None title: the plot title. Empty/None draws no title.
    :param line_width: series line width. Defaults to 2.
    :param fontsize: base font size. Defaults to Plotly's own default.
    :param bool show_sen: draw the Theil-Sen trend line on the Trend panel
    :param bool show_band: shade the dispersion band on the Observed panel
    :param list|None vlines: see plot.plot_result()
    """
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
    width = line_width or 2
    vertical_spacing = 0.3 / len(panels)
    date_axis_title = "Time step" if temporal_type == "relative" else "Date"

    fig = make_subplots(
        rows=len(panels), cols=1, shared_xaxes=True, vertical_spacing=vertical_spacing
    )

    # Indices of the crosshair shapes added below, one per row -- tracked
    # explicitly rather than assumed to be the array's first N entries,
    # since fig.add_hline() (the Residual zero-line, below) also inserts a
    # shape of its own, ahead of a row's crosshair shape in the very same
    # iteration, and shifts the simple "first N" assumption off by one.
    crosshair_shape_indices = []
    # One legend entry per category, shown on the first panel it is drawn
    # on (the rest repeat showlegend=False) -- the same approach as
    # plot.plot_result()'s own shared legend.
    legend_shown = set()
    for row, (panel_label, get_comp) in enumerate(panels, start=1):
        for index, category in enumerate(categories):
            comp = get_comp(category)
            label = category["label"]
            color = colors[index]
            show_legend = label not in legend_shown
            legend_shown.add(label)

            if panel_label == "Observed" and show_band:
                band_lower = category.get("band_lower")
                band_upper = category.get("band_upper")
                if band_lower is not None and band_upper is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=comp.index,
                            y=band_upper.values,
                            mode="lines",
                            line=dict(color=_rgba_string(color), width=0),
                            showlegend=False,
                            hoverinfo="skip",
                            meta={"category": label, "panel": panel_label},
                        ),
                        row=row,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=comp.index,
                            y=band_lower.values,
                            mode="lines",
                            line=dict(color=_rgba_string(color), width=0),
                            fill="tonexty",
                            fillcolor=_rgba_string(color, 0.15),
                            showlegend=False,
                            hoverinfo="skip",
                            meta={"category": label, "panel": panel_label},
                        ),
                        row=row,
                        col=1,
                    )

            if (
                panel_label == "Seasonal"
                and category.get("envelope_lower") is not None
                and category.get("envelope_upper") is not None
            ):
                for envelope in ("envelope_upper", "envelope_lower"):
                    fig.add_trace(
                        go.Scatter(
                            x=comp.index,
                            y=category[envelope].values,
                            mode="lines",
                            line=dict(color=_rgba_string(color), width=1, dash="dot"),
                            showlegend=False,
                            hoverinfo="skip",
                            meta={"category": label, "panel": panel_label},
                        ),
                        row=row,
                        col=1,
                    )

            if panel_label == "Residual":
                fig.add_trace(
                    go.Scatter(
                        x=comp.index,
                        y=comp.values,
                        mode="markers",
                        marker=dict(color=_rgba_string(color), size=4),
                        name=label,
                        legendgroup=label,
                        showlegend=show_legend,
                        meta={"category": label, "panel": panel_label},
                    ),
                    row=row,
                    col=1,
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=comp.index,
                        y=comp.values,
                        mode="lines",
                        line=dict(color=_rgba_string(color), width=width),
                        name=label,
                        legendgroup=label,
                        showlegend=show_legend,
                        meta={"category": label, "panel": panel_label},
                    ),
                    row=row,
                    col=1,
                )

            if panel_label == "Trend" and show_sen:
                for x_values, y_values in _sen_line_segments(
                    comp, category.get("trend_fit"), category.get("trend_fit_segments")
                ):
                    fig.add_trace(
                        go.Scatter(
                            x=x_values,
                            y=y_values,
                            mode="lines",
                            line=dict(color=_rgba_string(color), width=1, dash="dash"),
                            showlegend=False,
                            hoverinfo="skip",
                            meta={"category": label, "panel": panel_label},
                        ),
                        row=row,
                        col=1,
                    )

        if panel_label == "Residual":
            fig.add_hline(y=0, line=dict(color="grey", width=0.8), row=row, col=1)

        fig.update_yaxes(title_text=panel_label, row=row, col=1)
        fig.update_xaxes(showticklabels=(row == len(panels)), row=row, col=1)

        # One crosshair line per row, hidden until hovered (see
        # _INTERACTIVITY_SCRIPT's plotly_hover handler below). Plotly's own
        # per-axis spike lines (xaxis.showspikes) were tried first but only
        # extend within the subplot being hovered, not across the other
        # panels -- the whole point here -- so this draws it by hand
        # instead: a shape per row, whose x0/x1 the hover handler moves to
        # the hovered date and whose visibility it toggles. Row 1's axes are
        # plain 'x'/'y' (Plotly only numbers row 2 and up), same as the
        # vlines_label annotation below.
        axis_suffix = "" if row == 1 else str(row)
        crosshair_shape_indices.append(len(fig.layout.shapes))
        fig.add_shape(
            type="line",
            x0=0,
            x1=0,
            y0=0,
            y1=1,
            xref=f"x{axis_suffix}",
            yref=f"y{axis_suffix} domain",
            line=dict(color="#888", width=1, dash="dot"),
            visible=False,
        )
    fig.update_xaxes(
        title_text=date_axis_title,
        row=len(panels),
        col=1,
    )

    if vlines:
        for position, vline_label in vlines:
            for row in range(1, len(panels) + 1):
                fig.add_vline(
                    x=position,
                    line=dict(color="black", width=0.8, dash="dash"),
                    opacity=0.6,
                    row=row,
                    col=1,
                )
            if vline_label:
                # Row 1's axes are plain 'x'/'y' (Plotly only numbers row 2
                # and up), so the top panel is addressed directly here
                # rather than through add_annotation()'s row/col, which
                # would not let y be given in axes-fraction ("domain")
                # units while x stays in data units.
                fig.add_annotation(
                    x=position,
                    y=1.02,
                    xref="x",
                    yref="y domain",
                    text=vline_label,
                    showarrow=False,
                    textangle=-90,
                    xanchor="center",
                    yanchor="bottom",
                )

    fig.update_layout(
        title=title or None,
        # No fixed height: _INTERACTIVITY_SCRIPT instead sizes the chart to
        # the full browser window, so the panels use whatever vertical
        # space is actually available rather than a fixed guess. margin.b
        # is a fixed *pixel* reservation for the x-axis title and the
        # legend below it, below the plot area rather than a fraction of
        # it -- an axis's own 'domain' is a fraction of the plot area
        # *excluding* the margins, so a plain legend.y (which defaults to
        # the same "paper" reference as domain) would track the plot
        # area's height, not the fixed-size margin band it needs to land
        # in. yref="container" instead makes legend.y a fraction of the
        # *entire* figure, margins included, so y=0.01/yanchor="bottom"
        # means what it says: just above the literal bottom edge, at any
        # figure height.
        margin=dict(b=130, t=60 if title else 30),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            yref="container",
            xanchor="center",
            x=0.5,
        ),
        # One consolidated hover label at the shared x position, instead of
        # a separate tooltip per panel; paired with the per-row crosshair
        # shapes and _INTERACTIVITY_SCRIPT's plotly_hover handler above.
        hovermode="x unified",
        # Read by _INTERACTIVITY_SCRIPT's plotly_hover handler: the fixed
        # "first N shapes" ordering it would otherwise assume breaks
        # because fig.add_hline() (the Residual zero-line, above) also
        # inserts a shape, ahead of that row's own crosshair shape.
        meta={"crosshairShapeIndices": crosshair_shape_indices},
    )
    if fontsize:
        fig.update_layout(font=dict(size=fontsize))

    html = fig.to_html(
        include_plotlyjs="cdn",
        post_script=_INTERACTIVITY_SCRIPT,
        config={"responsive": True},
    )
    # fig.to_html() has no hook for extra page content, so the stats
    # sidebar -- plain HTML, not part of the Plotly figure -- is spliced
    # in around it instead: the chart (everything to.html() put inside
    # '<body>...</body>') is wrapped in the flex row's chart-area div by
    # splitting the insertion across the opening and closing body tags.
    stats_prefix, stats_suffix = _stats_sidebar_html(categories)
    if stats_prefix:
        html = html.replace("<body>", "<body>" + stats_prefix, 1)
        html = html.replace("</body>", stats_suffix + "</body>", 1)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)
        path_name = os.path.split(output)
        gs.message(
            _("Done, you can find the file {name} in {path}").format(
                name=path_name[1], path=path_name[0] or "."
            )
        )
    else:
        gs.message(_("Opening the plot in a browser tab..."))
        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(html)
            temp_path = f.name
        webbrowser.open(f"file://{temp_path}")
