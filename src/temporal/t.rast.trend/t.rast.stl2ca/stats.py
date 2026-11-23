############################################################################
#
# MODULE:       t.rast.stl2ca (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Per-category trend-statistics rows for t.rast.stl2ca's
#               stats_output= CSV and interactive.py's HTML stats table.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""Per-category trend-statistics rows for t.rast.stl2ca.

pd is set by t.rast.stl2ca.lazy_import_py_modules() -- after GRASS parses
the command line -- rather than imported here, so a plain module scan
(--help, g.extension) never needs pandas installed.
"""

import grass.script as gs

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by t.rast.stl2ca.lazy_import_py_modules() before any function below runs.
pd = None


def trend_stats_rows(categories):
    """Build one combined list of trend-statistics rows, one per category.

    Shared by write_trend_stats_csv() (below) and interactive.py's HTML
    stats table, so the two always report the same numbers the same way.

    A category fit with 'trend_fit_segments' (the breakpoints= option) gets
    one row per segment, each naming its own date/step range in the
    'segment' column, in addition to -- not instead of -- its whole-series
    row (segment=''); a category without breakpoints_opt has just the one,
    whole-series row.

    :param list categories: one dict per category, each with 'label' (str),
        'trend_fit' (trend.fit_trend() dict or None) and
        'trend_fit_segments' (list of (fit dict, segment label) pairs, or
        None), i.e. the same per-category dicts plot.plot_result() takes.
    :return list: dicts with keys category/segment/n_obs/unit/sen_slope/
        mk_tau/mk_pvalue
    """
    rows = []
    for category in categories:
        trend_fit = category.get("trend_fit")
        if trend_fit is not None:
            rows.append(_trend_stats_row(category["label"], "", trend_fit))
        for seg_fit, seg_label in category.get("trend_fit_segments") or []:
            rows.append(_trend_stats_row(category["label"], seg_label.strip(), seg_fit))
    return rows


def write_trend_stats_csv(categories, csv_path):
    """Write trend_stats_rows(categories) to one combined CSV file.

    t.rast.stl2ca.py does not expose the stats-in-legend plot option this
    addon used to have; this is its replacement, reporting the same
    Theil-Sen/Mann-Kendall numbers (already computed by fit_trend()
    regardless, whether or not a trend line is actually drawn) as a file
    instead of on the plot.

    :param list categories: see trend_stats_rows()
    :param str csv_path: output CSV path
    """
    rows = trend_stats_rows(categories)
    if not rows:
        gs.warning(_("No trend statistics to write to '{}'.").format(csv_path))
        return
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    gs.message(_("Trend statistics written to {}").format(csv_path))


def _trend_stats_row(label, segment, fit):
    """Build one write_trend_stats_csv() row from one fit_trend() result.

    OLS is deliberately left out here, even though fit_trend() always
    computes it (a negligible extra cost alongside Theil-Sen/Mann-Kendall,
    and e.g. t.rast.stl does report it): this addon's driver never exposes
    a way to draw the OLS line (no '-o' flag), so reporting its numbers in
    a CSV/table with nothing on the plot to relate them to would be
    confusing rather than useful.

    :param str label: category label
    :param str segment: segment label, or '' for the whole-series fit
    :param dict fit: a fit_trend() result dict
    :return dict: one CSV row
    """
    return {
        "category": label,
        "segment": segment,
        "n_obs": fit["x_stop"] - fit["x_start"] + 1,
        "unit": fit.get("unit_label"),
        "sen_slope": fit["sen_slope_report"],
        "mk_tau": fit["mk_tau"],
        "mk_pvalue": fit["mk_pvalue"],
    }
