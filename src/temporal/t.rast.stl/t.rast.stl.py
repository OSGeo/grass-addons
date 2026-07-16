#!/usr/bin/env python

############################################################################
#
# MODULE:       t.rast.stl
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Extracts the time series of a single point from a space-time
#               raster dataset (strds), regularizes it onto an evenly spaced
#               axis, runs an STL decomposition (seasonal / trend / remainder)
#               and produces a multi-panel plot.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: STL decomposition (seasonal/trend/remainder) of time series of selected point
# % keyword: temporal
# % keyword: raster
# % keyword: time series
# % keyword: decomposition
# % keyword: STL
# % keyword: plot
# % keyword: display
# %end

# %option G_OPT_STRDS_INPUT
# % key: strds
# % guisection: Input
# %end

# %option G_OPT_STRDS_INPUT
# % key: strds2
# % required: no
# % label: Second space-time raster dataset to compare
# % description: Optional second strds. When given, it is decomposed and trend-fitted like 'strds', and both are drawn on the same panels with 'strds2' on a twin right y-axis (its scale may differ). Both datasets must share the same temporal type.
# % guisection: Input
# %end

# %option G_OPT_M_COORDS
# % required: yes
# % label: Point coordinates (east,north)
# % description: Comma separated pair of map coordinates of the point to extract. In the GUI (launched from a Map Display) the value can be filled by clicking in the display.
# % guisection: Input
# %end

# %option
# % key: frequency
# % type: string
# % label: Target resampling frequency
# % description: Pandas offset alias for the regular time axis the series is resampled onto, e.g. D (day), W (week), MS (month start), 16D (16 days). Required for absolute-time strds.
# % required: no
# % guisection: Regularization
# %end

# %option
# % key: step
# % type: integer
# % label: Relative-time step (override)
# % description: Integer spacing of the regular axis for relative-time STRDS, in the dataset's own time unit. If omitted, the dataset granularity (from t.info) is used and the extent is taken from the data. Ignored for absolute-time STRDS (use 'frequency' instead).
# % required: no
# % guisection: Regularization
# %end

# %option
# % key: interpolation
# % type: string
# % label: Gap interpolation method
# % description: Method passed to pandas Series.interpolate() to fill gaps after resampling.
# % options: linear,time,nearest,zero,slinear,quadratic,cubic,spline,polynomial,pchip,akima
# % answer: linear
# % required: no
# % guisection: Regularization
# %end

# %option
# % key: order
# % type: integer
# % label: Interpolation order
# % description: Order for the spline/polynomial interpolation methods (ignored otherwise).
# % required: no
# % guisection: Regularization
# %end

# %option
# % key: period
# % type: integer
# % label: Seasonal period
# % description: Number of observations per seasonal cycle (statsmodels STL 'period'). If not set, inferred from the resampled DatetimeIndex frequency.
# % required: no
# % guisection: STL
# %end

# %option
# % key: seasonal
# % type: integer
# % label: Seasonal smoother length
# % description: Length of the seasonal LOESS smoother (statsmodels STL 'seasonal'). Must be an odd integer >= 7. If not set, inferred from data.
# % required: no
# % guisection: STL
# %end

# %option
# % key: trend
# % type: integer
# % label: Trend smoother length
# % description: Length of the trend LOESS smoother (statsmodels STL 'trend'). Must be an odd integer. If not set, inferred from data.
# % required: no
# % guisection: STL
# %end

# %option
# % key: low_pass
# % type: integer
# % label: Low-pass smoother length
# % description: Length of the low-pass LOESS smoother (statsmodels STL 'low_pass'). Must be an odd integer >= 3. Defaults to the smallest odd integer > period.
# % required: no
# % guisection: STL
# %end

# %option
# % key: seasonal_degree
# % type: integer
# % label: Seasonal LOESS degree
# % description: Degree of the seasonal LOESS polynomial (statsmodels STL 'seasonal_deg'). Default is 1.
# % options: 0,1
# % answer: 1
# % required: no
# % guisection: STL
# %end

# %option
# % key: trend_degree
# % type: integer
# % label: Trend LOESS degree
# % description: Degree of the trend LOESS polynomial (statsmodels STL 'trend_deg'). Default is 1.
# % options: 0,1
# % answer: 1
# % required: no
# % guisection: STL
# %end

# %option
# % key: low_pass_degree
# % type: integer
# % label: Low-pass LOESS degree
# % description: Degree of the low-pass LOESS polynomial (statsmodels STL 'low_pass_deg'). Default is 1.
# % options: 0,1
# % answer: 1
# % required: no
# % guisection: STL
# %end

# %option
# % key: seasonal_jump
# % type: integer
# % label: Seasonal jump
# % description: Positive integer step the seasonal LOESS is evaluated at, interpolating in between (statsmodels STL 'seasonal_jump'). Higher is faster, less exact. Default is 1.
# % answer: 1
# % required: no
# % guisection: STL
# %end

# %option
# % key: trend_jump
# % type: integer
# % label: Trend jump
# % description: Positive integer step the trend LOESS is evaluated at (statsmodels STL 'trend_jump'). Default is 1.
# % answer: 1
# % required: no
# % guisection: STL
# %end

# %option
# % key: low_pass_jump
# % type: integer
# % label: Low-pass jump
# % description: Positive integer step the low-pass LOESS is evaluated at (statsmodels STL 'low_pass_jump'). Default is 1.
# % answer: 1
# % required: no
# % guisection: STL
# %end

# %flag
# % key: r
# % label: Robust STL fitting
# % description: Use robust (data-dependent) weighting in the STL fit (statsmodels STL robust=True).
# % guisection: STL
# %end

# %flag
# % key: o
# % label: OLS trend line
# % description: Add the ordinary least-squares (OLS) regression line (slope and R^2) to the trend panel.
# % guisection: Trend line
# %end

# %flag
# % key: s
# % label: Theil-Sen trend line
# % description: Add the robust Theil-Sen regression line (slope and Mann-Kendall p-value) to the trend panel.
# % guisection: Trend line
# %end

# %flag
# % key: g
# % label: GAM trend curve
# % description: Add a shape-constrained (monotone) Generalized Additive Model trend curve (pyGAM) to the trend panel. Requires the 'pygam' package.
# % guisection: Trend line
# %end

# %flag
# % key: b
# % label: GAM confidence band
# % description: Shade the 95% confidence band of the monotone GAM curve (only used together with -g).
# % guisection: Trend line
# %end

# %flag
# % key: t
# % label: Trend-line statistics in plot
# % description: Show the trend-line statistics (slope, R^2, Mann-Kendall p-value, GAM net change) in the plot legend. They are always printed to the terminal regardless of this flag.
# % guisection: Trend line
# %end

# %option
# % key: gam_direction
# % type: string
# % label: GAM monotonic direction
# % description: Direction of the monotonicity constraint for the GAM trend curve. 'auto' picks increasing or decreasing from the sign of the Theil-Sen slope.
# % options: auto,increasing,decreasing
# % answer: auto
# % required: no
# % guisection: Trend line
# %end

# %option
# % key: slope_unit
# % type: string
# % label: Reporting unit for trend slopes
# % description: Time unit the reported OLS/Theil-Sen slopes and the GAM net change are expressed per (value change per unit). 'auto' picks a readable calendar unit (day/week/month/year) from the series span for absolute-time data; 'step' keeps the value change per observation step (per frequency/step). For relative-time data only 'auto' and 'step' apply.
# % options: auto,step,day,week,month,year
# % answer: auto
# % required: no
# % guisection: Trend line
# %end

# %option
# % key: trend_trim
# % type: string
# % label: Trend regression edge trim
# % description: How much of each end of the trend component to drop before fitting the trend regression, expressed as a fraction of the STL trend-smoother window. See below for more details.
# % options: none,0.1,0.25,0.5,1
# % answer: none
# % required: no
# % guisection: STL
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % required: no
# % label: Name of output plot file
# % description: Output image file. The format is taken from the extension (e.g. .png, .pdf, .svg). If omitted, the plot is shown in an interactive window.
# % guisection: Output
# %end

# %option
# % key: backend
# % type: string
# % label: Matplotlib backend
# % description: Matplotlib rendering backend. WXAgg (default) opens an interactive window. Agg is non-interactive and used automatically when saving to a file.
# % options: WXAgg,TkAgg,Qt5Agg,GTK3Agg,Agg
# % required: no
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key: csv
# % required: no
# % label: Name output CSV file
# % description: Optional CSV file with the observed, trend, seasonal and residual components per date.
# % guisection: Output
# %end

# %option G_OPT_V_OUTPUT
# % key: vector
# % required: no
# % label: Name output point vector layer
# % description: Optional name of a point vector layer to create at the selected location.
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Plot resolution in DPI.
# % answer: 300
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
# % key: style
# % type: string
# % label: Matplotlib style
# % description: Matplotlib style sheet, see https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
# % required: no
# % guisection: Output
# %end

# %option
# % key: fontsize
# % type: double
# % label: Font size
# % description: Base font size of plot text. Defaults to the Matplotlib/style default.
# % required: no
# % guisection: Output
# %end

# %option
# % key: line_width
# % type: double
# % label: Line width
# % description: Width of the series lines. Defaults to the Matplotlib default.
# % required: no
# % guisection: Output
# %end

# %option
# % key: title
# % type: string
# % label: Plot title
# % description: The title of the plot. If left empty, no title is drawn.
# % required: no
# % guisection: Aesthetics
# %end

# %flag
# % key: y
# % label: Use a common y-axis scale for both datasets
# % description: When two datasets are plotted, force both to share the same y-axis range on each panel instead of giving 'strds2' its own (right) axis. Only meaningful with strds2; most useful when the two datasets are in comparable units.
# % guisection: Optional
# %end

# %option G_OPT_CN
# % key: color
# % type: string
# % label: Line color for the first dataset
# % description: Color of the 'strds' series lines. Accepts a GRASS color name (e.g. 'blue'), an R:G:B triplet (e.g. '0:0:255'), or any matplotlib color such as a hex code ('#1f77b4') or 'tab:' name. The trend-regression lines for this dataset are drawn in a matching darker/lighter family. Defaults to the Matplotlib default.
# % required: no
# % answer:
# % guisection: Optional
# %end

# %option G_OPT_CN
# % key: color2
# % type: string
# % label: Line color for the second dataset
# % description: Color of the 'strds2' series lines. Accepts a GRASS color name, an R:G:B triplet, or any matplotlib color (hex code or 'tab:' name). Used only when strds2 is given. Its trend-regression lines use a matching family. Defaults to the Matplotlib default.
# % required: no
# % answer:
# % guisection: Optional
# %end

# %option G_OPT_M_NPROCS
# %end

# %option G_OPT_T_WHERE
# %end

# %rules
# % requires: -b, -g
# % requires: gam_direction, -g
# % requires: -y, strds2
# %end


import atexit
import colorsys
import importlib.util
import os
import sys

import grass.script as gs
from grass.exceptions import CalledModuleError

if not callable(globals().get("_")):
    from gettext import gettext as _


# Directories created with gs.tempdir() during the run, removed by cleanup().
clean_dirs = []


def cleanup():
    """Remove temporary directories registered during the run."""
    for path in clean_dirs:
        gs.try_rmdir(path)


def lazy_import_py_modules(backend="WXAgg"):
    """Lazy import of the third-party scientific stack.

    :param str backend: matplotlib backend to activate before importing pyplot
    """
    global np
    global pd
    global STL
    global linregress
    global theilslopes
    global kendalltau
    global mpl
    global plt

    try:
        import numpy as np
        import pandas as pd
    except ModuleNotFoundError as e:
        gs.fatal(
            _(
                "The Python package '{pkg}' is required but not installed. "
                "Install it with e.g. 'pip install numpy pandas'."
            ).format(pkg=e.name)
        )

    try:
        from statsmodels.tsa.seasonal import STL as _STL

        STL = _STL
    except ModuleNotFoundError:
        gs.fatal(
            _(
                "The Python package 'statsmodels' is required for the STL "
                "decomposition but is not installed. Install it with e.g. "
                "'pip install statsmodels'."
            )
        )

    try:
        from scipy.stats import (
            kendalltau as _kendalltau,
            linregress as _linregress,
            theilslopes as _theilslopes,
        )
    except ModuleNotFoundError:
        gs.fatal(
            _(
                "The Python package 'scipy' is required for the trend "
                "regression but is not installed. Install it with e.g. "
                "'pip install scipy'."
            )
        )

    linregress = _linregress
    theilslopes = _theilslopes
    kendalltau = _kendalltau

    try:
        import matplotlib as mpl

        mpl.use(backend)
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is required but not installed. Please install it."))


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


def lazy_import_pygam():
    """Lazy import of pyGAM, only needed when the monotone GAM curve is requested.

    :return tuple: (LinearGAM, s) classes/functions from pygam
    """
    try:
        from pygam import LinearGAM, s as gam_s

        return LinearGAM, gam_s
    except ImportError as e:
        gs.fatal(
            _(
                "The Python package 'pygam' is required for the monotone GAM "
                "trend curve (flag -g) but could not be imported ({err}). "
                "Install it with e.g. 'pip install pygam', or drop the -g "
                "flag."
            ).format(err=e)
        )


def coords_from_option(coordinates):
    """Parse the coordinates= option into an (east, north) float pair.

    :param str coordinates: "east,north" as given on the command line
    :return tuple: (east, north) as floats
    """
    parts = coordinates.split(",")
    if len(parts) != 2:
        gs.fatal(_("The coordinates option must be a single 'east,north' pair."))
    try:
        east, north = float(parts[0]), float(parts[1])
    except ValueError:
        gs.fatal(_("Could not parse coordinates '{}' as numbers.").format(coordinates))
    return (east, north)


def extract_series(strds, east, north, where, null_value="nan", nprocs=1):
    """Extract a (date, value) series for one point from an strds.

    Uses t.rast.what with layout=row so each registered timestep yields one
    row of the form "start|end|value" (with -n adding a header row).

    :param str strds: name of the input space-time raster dataset
    :param float east: easting of the point
    :param float north: northing of the point
    :param str where: optional t.* WHERE clause to subset maps
    :param str null_value: token used by t.rast.what for NULL pixel values
    :param int nprocs: number of parallel r.what processes for t.rast.what

    :return tuple: (list_of_start_datetimes_as_str, list_of_float_or_None)
    """
    kwargs = {
        "strds": strds,
        "coordinates": [east, north],
        "layout": "row",
        "null_value": null_value,
        "flags": "n",  # header row, so we can find columns by name
        "separator": "pipe",
        "nprocs": nprocs,
    }
    if where:
        kwargs["where"] = where

    # t.rast.what assembles its result into the file given by output=, but for
    # long series it also seems to write intermediate r.what text files. It is
    # not clear how to avoid that, so a temporary directory is used as the working
    # directory and the assembled result is written to a file in that same
    # directory. The directory is registered for removal by the atexit
    # cleanup() handler.
    tmpdir = gs.tempdir()
    clean_dirs.append(tmpdir)
    out_file = os.path.join(tmpdir, "series.txt")
    try:
        gs.run_command(
            "t.rast.what",
            cwd=tmpdir,
            overwrite=True,
            output=out_file,
            **kwargs,
        )
    except CalledModuleError:
        gs.fatal(
            _(
                "t.rast.what failed while sampling strds '{}'. Check that "
                "the dataset exists, that the point falls within the "
                "current computational region, and that the region "
                "resolution is set (see g.region)."
            ).format(strds)
        )
    try:
        with open(out_file) as fh:
            raw = fh.read()
    except OSError:
        gs.fatal(_("t.rast.what produced no output file for the point."))

    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        gs.fatal(_("t.rast.what returned no data for the given point."))

    header = lines[0].split("|")
    # Row layout for a single point: x|y|start|end|value
    try:
        start_idx = header.index("start")
    except ValueError:
        # Fall back to position.
        start_idx = 2 if len(header) >= 5 else 0
    value_idx = len(header) - 1

    dates = []
    values = []
    for ln in lines[1:]:
        cols = ln.split("|")
        if len(cols) <= value_idx:
            continue
        dates.append(cols[start_idx])
        token = cols[value_idx]
        if token in (null_value, "", "*", "None"):
            values.append(None)
        else:
            try:
                values.append(float(token))
            except ValueError:
                values.append(None)

    if not dates:
        gs.fatal(_("Could not parse any timesteps from t.rast.what output."))
    return (dates, values)


def build_series(dates, values, temporal_type="absolute"):
    """Build a pandas Series indexed by datetime (absolute) or integer (relative).

    :param list dates: list of date strings (absolute) or integer strings (relative)
    :param list values: corresponding float values
    :param str temporal_type: 'absolute' or 'relative'
    :return pandas.Series: float series sorted by index
    """
    if temporal_type == "relative":
        idx = pd.Index([int(d) for d in dates], dtype="int64")
    else:
        idx = pd.to_datetime(dates, format="mixed")
    s = pd.Series(values, index=idx, dtype="float64").sort_index()
    s = s[~s.index.duplicated(keep="first")]
    return s


def resolve_relative_step(series, step_opt, tinfo):
    """Determine the integer spacing of the regular axis for a relative STRDS.

    Priority: explicit 'step' option > dataset granularity (t.info) > fatal.

    :param pandas.Series series: irregular point series (integer index)
    :param str step_opt: the step= option value (may be empty)
    :param dict|None tinfo: parsed t.info -g output

    :return int: positive integer step
    """
    if step_opt:
        step = int(step_opt)
        if step <= 0:
            gs.fatal(_("The 'step' option must be a positive integer."))
        gs.message(_("Using user-supplied relative step of {}.").format(step))
        return step
    if tinfo:
        gran = str(tinfo.get("granularity", "")).strip()
        if gran.isdigit() and int(gran) > 0:
            gs.message(
                _("Using STRDS granularity of {} as the relative step.").format(gran)
            )
            return int(gran)
    gs.fatal(
        _(
            "Could not determine the regular spacing for this relative STRDS. "
            "The granularity was not available from t.info; please set the "
            "'step' option explicitly (integer, in the dataset's time unit)."
        )
    )


def regularize(
    series, frequency, method, order, temporal_type="absolute", step=None, tinfo=None
):
    """Resample onto a regular axis and interpolate gaps.

    STL requires an evenly spaced, gap-free series. To ensure this, data is resampled
    to the target frequency and interpolated.

    For relative STRDS the index is an integer sequence. The grid step comes
    from the 'step' option or the dataset granularity, the extent comes from
    the observed values, and any observation that does not land on a grid
    node is snapped to the nearest node with a warning.

    :param pandas.Series series: irregular point series
    :param str frequency: pandas offset alias (e.g. 'MS', '16D'); may be empty.
        Ignored for relative STRDS.
    :param str method: pandas interpolate() method
    :param int|None order: order for spline/polynomial methods
    :param str temporal_type: 'absolute' or 'relative'
    :param str|None step: relative-time step override (option value)
    :param dict|None tinfo: parsed t.info -g output (relative granularity)

    :return pandas.Series: regular, gap-free series
    """
    if temporal_type == "relative":
        step_val = resolve_relative_step(series, step, tinfo)
        # Anchor the grid to the dataset start when available (so the lattice
        # phase matches the STRDS), else to the first observation. The top is
        # the last observation to avoid a non-existing trailing node.
        origin = int(series.index.min())
        if tinfo:
            start_meta = str(tinfo.get("start_time", "")).strip()
            try:
                origin = int(start_meta)
            except (TypeError, ValueError):
                pass
        last = int(series.index.max())
        # Build nodes from origin up to and including the last observation.
        # Cap strictly at 'last' so an interval STRDS's end_time (one step
        # beyond the final map start) cannot introduce a non-existing
        # trailing node.
        n_nodes = (last - origin) // step_val + 1
        nodes = origin + np.arange(n_nodes) * step_val
        nodes = nodes[nodes <= last]
        full_idx = pd.Index(nodes.astype("int64"))

        # Snap each observation to its nearest grid node. Off-grid points are
        # warned about and re-labelled rather than dropped on reindex.
        offsets = series.index.to_numpy() - origin
        snapped = origin + np.round(offsets / step_val).astype("int64") * step_val
        off_grid = int((snapped != series.index.to_numpy()).sum())
        if off_grid:
            gs.warning(
                _(
                    "{n} of {t} observation(s) did not fall on the regular "
                    "step={s} grid and were snapped to the nearest grid node."
                ).format(n=off_grid, t=len(series), s=step_val)
            )
        snapped_series = pd.Series(series.to_numpy(), index=pd.Index(snapped))
        # If two observations are on the same node, they are averaged
        snapped_series = snapped_series.groupby(level=0).mean()
        resampled = snapped_series.reindex(full_idx)
    elif frequency:
        resampled = series.resample(frequency).mean()
    else:
        # Try to use the inferred frequency of the index.
        inferred = pd.infer_freq(series.index)
        if inferred is None:
            gs.fatal(
                _(
                    "No 'frequency' was given and the series spacing could not "
                    "be inferred. Please set the frequency option (e.g. 'MS', "
                    "'16D')."
                )
            )
        resampled = series.asfreq(inferred)

    interp_kwargs = {"method": method, "limit_direction": "both"}
    if method in ("spline", "polynomial"):
        if not order:
            gs.fatal(
                _("The '{}' interpolation method requires the 'order' option.").format(
                    method
                )
            )
        interp_kwargs["order"] = int(order)

    filled = resampled.interpolate(**interp_kwargs)
    # Edge gaps that interpolation could not reach: back/forward fill.
    filled = filled.bfill().ffill()

    if filled.isna().any():
        gs.fatal(_("Series still contains gaps after interpolation; cannot run STL."))
    if len(filled) < 4:
        gs.fatal(
            _("Too few observations ({}) after regularization to run STL.").format(
                len(filled)
            )
        )
    return filled


def infer_period(series, period_opt, temporal_type="absolute", tinfo=None):
    """Determine the STL seasonal period.

    :param pandas.Series series: regularized series
    :param str period_opt: the period= option value (may be empty)
    :param str temporal_type: 'absolute' or 'relative'
    :param dict|None tinfo: parsed t.info -g output (used for relative STRDS)

    :return int: seasonal period (number of observations per cycle)
    """
    if period_opt:
        return int(period_opt)

    if temporal_type == "relative":
        # Try to derive period from granularity + unit reported by t.info.
        per_year_by_unit = {
            "seconds": 365 * 24 * 3600,
            "minutes": 365 * 24 * 60,
            "hours": 24,
            "days": 365,
            "weeks": 52,
            "months": 12,
            "years": 1,
        }
        if tinfo:
            unit = tinfo.get("unit", "").strip().lower().rstrip("s") + "s"
            granularity = tinfo.get("granularity", "").strip()
            if unit in per_year_by_unit and granularity.isdigit():
                per_year = per_year_by_unit[unit]
                period = max(2, round(per_year / int(granularity)))
                gs.message(
                    _(
                        "Inferred seasonal period of {} from STRDS granularity ({} {})."
                    ).format(period, granularity, unit)
                )
                return period
        gs.fatal(
            _(
                "Cannot infer a seasonal period for this relative STRDS. "
                "Please set the 'period' option explicitly (e.g. the number "
                "of observations per seasonal cycle)."
            )
        )

    freq = getattr(series.index, "freqstr", None)
    if freq is None:
        gs.fatal(
            _(
                "Could not infer a seasonal period from the series frequency. "
                "Please set the 'period' option explicitly."
            )
        )
    # Map common pandas offset aliases to an annual seasonal period.
    base = "".join(ch for ch in freq if ch.isalpha()).upper()
    mult = "".join(ch for ch in freq if ch.isdigit())
    mult = int(mult) if mult else 1
    per_year = {
        "D": 365,
        "B": 252,
        "W": 52,
        # "M"/"Q" are the legacy month-/quarter-end aliases (pandas < 2.2); they
        # were deprecated in 2.2 and removed in favour of "ME"/"QE". "MS"/"QS"
        # (month-/quarter-start) are unchanged across versions. All are listed so
        # frequencies entered against either pandas generation works.
        "M": 12,
        "MS": 12,
        "ME": 12,
        "Q": 4,
        "QS": 4,
        "QE": 4,
        "H": 24,
    }
    if base in per_year:
        period = max(2, round(per_year[base] / mult))
        gs.message(
            _("Inferred seasonal period of {} from frequency '{}'.").format(
                period, freq
            )
        )
        return period
    gs.fatal(
        _(
            "Could not infer a seasonal period from frequency '{}'. "
            "Please set the 'period' option explicitly."
        ).format(freq)
    )


def run_stl(
    series,
    period,
    seasonal,
    trend,
    low_pass,
    seasonal_deg,
    trend_deg,
    low_pass_deg,
    seasonal_jump,
    trend_jump,
    low_pass_jump,
    robust,
):
    """Run the statsmodels STL decomposition.

    Only the window-length parameters (seasonal, trend, low_pass) are passed
    when set. Otherwise, statsmodels' own auto-defaults apply.

    :return statsmodels DecomposeResult: with .observed/.trend/.seasonal/.resid
    """

    kwargs = {
        "period": period,
        "robust": robust,
        "seasonal_deg": int(seasonal_deg),
        "trend_deg": int(trend_deg),
        "low_pass_deg": int(low_pass_deg),
        "seasonal_jump": int(seasonal_jump),
        "trend_jump": int(trend_jump),
        "low_pass_jump": int(low_pass_jump),
    }

    # Window lengths and jumps are validated up front in validate_options().
    if seasonal:
        kwargs["seasonal"] = validate_odd_window(seasonal, "seasonal", 7)
    if trend:
        kwargs["trend"] = validate_odd_window(trend, "trend", 3)
    if low_pass:
        kwargs["low_pass"] = validate_odd_window(low_pass, "low_pass", 3)

    for key in ("seasonal_jump", "trend_jump", "low_pass_jump"):
        if kwargs[key] < 1:
            gs.fatal(_("'{}' must be a positive integer.").format(key))

    try:
        return STL(series, **kwargs).fit()
    except ValueError as e:
        gs.fatal(_("STL decomposition failed: {}").format(e))


def effective_trend_window(period, seasonal, trend):
    """Return the trend LOESS window length statsmodels actually uses.

    When the user sets ``trend`` explicitly, that value is used. Otherwise
    statsmodels derives it from period and seasonal with the formula from the
    original STL implementation: the smallest odd integer greater than
    ``1.5 * period / (1 - 1.5 / seasonal)``. The seasonal window in that
    formula is itself statsmodels' default (7) when the user left it unset.

    The trend-window-based edge trim has to know the resolved trend window,
    but the fitted STL object does not provide it (as far as I can see).

    :param int period: seasonal period
    :param seasonal: user seasonal window or falsy for the statsmodels default
    :param trend: user trend window or falsy to derive it
    :return int: the effective (odd) trend window length
    """
    if trend:
        return int(trend)
    seasonal = int(seasonal) if seasonal else 7
    raw = 1.5 * period / (1.0 - 1.5 / seasonal)
    win = int(np.ceil(raw))
    if win % 2 == 0:
        win += 1
    return win


# Length of one calendar reporting unit, in days. Used to convert a
# per-step slope to a per-day/week/month/year slope. Month and year use the
# mean Gregorian length so the conversion is independent of which month or
# year the series happens to cover.
_UNIT_DAYS = {
    "day": 1.0,
    "week": 7.0,
    "month": 365.2425 / 12.0,
    "year": 365.2425,
}


def clean_granularity(tinfo):
    """Return the t.info granularity string, stripped of quotes/whitespace.

    t.info -g may report the granularity quoted (e.g. "'1 month'"); strip the
    surrounding quotes so it parses as "1 month".

    :param dict|None tinfo: parsed t.info -g output
    :return str: cleaned granularity (possibly empty)
    """
    if not tinfo:
        return ""
    return str(tinfo.get("granularity", "")).strip().strip("'\"").strip()


def step_length_days(frequency, tinfo):
    """Length of one regularized observation step, in days, for absolute time.

    Derived from the resampling 'frequency' (a pandas offset alias such as
    'D', 'W', 'MS', '16D'). When 'frequency' is empty (a regularly spaced
    absolute STRDS resampled on its inferred frequency), the granularity from
    t.info is used as a fallback.

    :param str frequency: pandas offset alias (may be empty)
    :param dict|None tinfo: parsed t.info -g output
    :return float|None: step length in days, or None if it cannot be determined
    """
    days_per_unit = {
        "D": 1.0,
        "B": 1.0,
        "W": 7.0,
        "M": 365.2425 / 12.0,
        "MS": 365.2425 / 12.0,
        "ME": 365.2425 / 12.0,
        "Q": 365.2425 / 4.0,
        "QS": 365.2425 / 4.0,
        "Y": 365.2425,
        "YS": 365.2425,
        "A": 365.2425,
        "AS": 365.2425,
        "H": 1.0 / 24.0,
    }
    freq = frequency
    if not freq and tinfo:
        # Fall back to the dataset granularity, e.g. "1 months", "16 days".
        gran = clean_granularity(tinfo).lower()
        parts = gran.split()
        if len(parts) == 2 and parts[0].isdigit():
            n = int(parts[0])
            unit = parts[1].rstrip("s")
            per = {
                "second": 1.0 / 86400.0,
                "minute": 1.0 / 1440.0,
                "hour": 1.0 / 24.0,
                "day": 1.0,
                "week": 7.0,
                "month": 365.2425 / 12.0,
                "year": 365.2425,
            }.get(unit)
            if per is not None:
                return n * per
        return None
    if not freq:
        return None
    base = "".join(ch for ch in freq if ch.isalpha()).upper()
    mult = "".join(ch for ch in freq if ch.isdigit())
    mult = int(mult) if mult else 1
    if base in days_per_unit:
        return mult * days_per_unit[base]
    return None


def slope_unit_scale(slope_unit, temporal_type, frequency, step, tinfo, n_obs):
    """Resolve the slope reporting unit into a (scale, label) pair.

    The trend regressions are fitted in index space, so a raw slope is a value
    change *per observation step*. Multiplying it by the returned ``scale``
    converts it to a value change per chosen calendar unit (day/week/month/
    year), independent of the resampling frequency and therefore comparable
    across runs (see fit_trend for which quantities the scale is applied to).

    For absolute-time data 'step' returns scale 1.0, the fixed calendar units
    return their exact conversion, and 'auto' picks the largest of day/week/
    month/year over which the series spans at least a few units.

    :param str slope_unit: the slope_unit= option ('auto','step','day',...)
    :param str temporal_type: 'absolute' or 'relative'
    :param str frequency: the frequency= option (absolute time)
    :param str step: the step= option (relative time)
    :param dict|None tinfo: parsed t.info -g output
    :param int n_obs: number of observations in the regularized series
    :return tuple: (float scale, str unit_label)
    """
    if temporal_type == "relative":
        # Relative time has no guaranteed calendar mapping, but GRASS relative
        # STRDS still carry a named time unit (days/weeks/months/years/...).
        # When that unit is a recognized calendar unit we can convert the
        # per-step slope to a readable unit exactly as for absolute time;
        # otherwise we report per step.
        unit = ""
        gran = ""
        if tinfo:
            unit = str(tinfo.get("unit", "")).strip().strip("'\"").lower().rstrip("s")
            gran = clean_granularity(tinfo)
        # Step size in the dataset's own time unit: explicit step= wins, else
        # the granularity count, else 1.
        try:
            step_units = int(step) if step else (int(gran) if gran.isdigit() else 1)
        except (TypeError, ValueError):
            step_units = 1
        unit_days = _UNIT_DAYS.get(unit)
        if unit_days is not None:
            # One step is step_units * unit_days long; reuse the same logic as
            # absolute time so 'auto'/'day'/'week'/'month'/'year' all work.
            step_days = step_units * unit_days
            return resolve_calendar_unit(
                slope_unit,
                step_days,
                n_obs,
                fallback_label=unit_label(step_units, unit),
            )
        # Unknown / non-calendar unit: per step only.
        return 1.0, unit_label(step_units, unit or "step")

    step_days = step_length_days(frequency, tinfo)
    if step_days is None and slope_unit in _UNIT_DAYS:
        gs.warning(
            _(
                "Could not determine the step length in days; reporting "
                "trend slopes per observation step instead of per {u}."
            ).format(u=slope_unit)
        )
    return resolve_calendar_unit(
        slope_unit, step_days, n_obs, fallback_label=step_label(frequency, tinfo)
    )


def resolve_calendar_unit(slope_unit, step_days, n_obs, fallback_label):
    """Convert a per-step slope to a per-calendar-unit slope.

    Shared by the absolute-time path and the relative-time path when the
    dataset's time unit is a recognized calendar unit. Returns a (scale, label)
    pair where multiplying a per-step slope by ``scale`` gives the value change
    per the chosen unit.

    :param str slope_unit: 'auto', 'step', 'day', 'week', 'month' or 'year'
    :param float|None step_days: length of one observation step in days, or
        None if it could not be determined
    :param int n_obs: number of observations (for 'auto' span selection)
    :param str fallback_label: label to use when reporting per step
    :return tuple: (float scale, str unit_label)
    """
    # Per step, or step length unknown: no conversion.
    if slope_unit == "step" or step_days is None or step_days <= 0:
        return 1.0, fallback_label

    # Explicit calendar unit.
    if slope_unit in _UNIT_DAYS:
        return _UNIT_DAYS[slope_unit] / step_days, slope_unit

    # 'auto' (or anything unexpected): pick the largest unit the series spans
    # at least ~3 of, so the slope is over a unit comparable to the data extent
    # without being tiny.
    span_days = max(0.0, (n_obs - 1)) * step_days
    for unit in ("year", "month", "week", "day"):
        if span_days >= 3.0 * _UNIT_DAYS[unit]:
            return _UNIT_DAYS[unit] / step_days, unit
    # Very short series: report per day.
    return _UNIT_DAYS["day"] / step_days, "day"


def unit_label(count, unit):
    """Format a (count, unit) pair as a clean per-unit label.

    A count of 1 is dropped and the unit is singular ('month', 'day'); a count
    greater than 1 keeps the plural ('3 months', '16 days').

    :param int count: number of base units per step
    :param str unit: singular unit name (e.g. 'month'); may be '' or 'step'
    :return str: e.g. 'month', '3 months', 'step'
    """
    unit = (unit or "step").rstrip("s")
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 1
    if count <= 1:
        return unit
    return "{} {}s".format(count, unit)


def step_label(frequency, tinfo):
    """Human label for one observation step (used when reporting per step).

    Turns a pandas offset alias into a clean unit name: 'MS' -> 'month',
    'W' -> 'week', '16D' -> '16 days', 'D' -> 'day'. Falls back to the t.info
    granularity (e.g. '1 months' -> 'month', '16 days' -> '16 days') and then
    to a generic 'step'.

    :param str frequency: the frequency= option (absolute time)
    :param dict|None tinfo: parsed t.info -g output
    :return str: e.g. 'month', '16 days', 'step'
    """
    # Map an offset alias base to a singular unit name.
    alias_unit = {
        "D": "day",
        "B": "day",
        "W": "week",
        "M": "month",
        "MS": "month",
        "ME": "month",
        "Q": "quarter",
        "QS": "quarter",
        "Y": "year",
        "YS": "year",
        "A": "year",
        "AS": "year",
        "H": "hour",
    }
    if frequency:
        base = "".join(ch for ch in frequency if ch.isalpha()).upper()
        mult = "".join(ch for ch in frequency if ch.isdigit())
        mult = int(mult) if mult else 1
        unit = alias_unit.get(base)
        if unit:
            return unit_label(mult, unit)
        return "{} step".format(frequency)
    if tinfo:
        gran = clean_granularity(tinfo)
        parts = gran.split()
        if len(parts) == 2 and parts[0].isdigit():
            return unit_label(int(parts[0]), parts[1].rstrip("s"))
        if gran:
            return "{} step".format(gran)
    return "step"


def format_slope(value, unit_label=None):
    """Format a slope as a plain decimal (no scientific notation).

    This picks enough decimal places to show four significant figures of the
    value. When ``unit_label`` is given it is appended as a per-unit suffix,
    e.g. '0.0231 /year'.

    :param float value: slope value
    :param str|None unit_label: reporting unit (e.g. 'year', '16D step'); when
        given, a ' /<unit>' suffix is appended
    :return str: fixed-point string, e.g. '0.00006489' or '0.0231 /year'
    """
    if value == 0 or not np.isfinite(value):
        text = "{:.4f}".format(value)
    else:
        # Decimals needed so the first significant digit plus 3 more are shown.
        leading = int(np.floor(np.log10(abs(value))))
        decimals = max(4, 3 - leading)
        text = "{:.{d}f}".format(value, d=decimals)
    if unit_label:
        text = "{} /{}".format(text, unit_label)
    return text


def write_csv(result, csv_path, temporal_type="absolute"):
    """Write the decomposition components to a CSV file."""
    df = pd.DataFrame(
        {
            "observed": result.observed,
            "trend": result.trend,
            "seasonal": result.seasonal,
            "residual": result.resid,
        }
    )
    df.index.name = "time_step" if temporal_type == "relative" else "date"
    df.to_csv(csv_path)
    gs.message(_("Components written to {}").format(csv_path))


def fit_gam(xm, ym, direction, sen_slope):
    """Fit a shape-constrained (monotone) GAM to (xm, ym) with pyGAM.

    A single smooth term on time is fit under a monotonic-increasing or
    monotonic-decreasing constraint. When ``direction`` is 'auto', the sign of
    the Theil-Sen slope decides the direction (a flat/zero Sen slope defaults to
    increasing). The fit is on the deseasonalized observed series.

    :param numpy.ndarray xm: observation indices (x), NaNs already removed
    :param numpy.ndarray ym: deseasonalized values (y), NaNs already removed
    :param str direction: 'auto', 'increasing' or 'decreasing'
    :param float sen_slope: Theil-Sen slope, used to resolve 'auto'
    :return dict|None: GAM results, or None if the fit could not be made. Keys:
        'fitted' (curve at each xm), 'lower'/'upper' (95% band at each xm or
        None), 'x' (the xm used), 'direction' (the resolved direction),
        'change' (fitted end minus fitted start over the span), 'pseudo_r2'.
    """
    LinearGAM, gam_s = lazy_import_pygam()

    if direction == "auto":
        resolved = "decreasing" if sen_slope < 0 else "increasing"
    else:
        resolved = direction
    constraint = "monotonic_inc" if resolved == "increasing" else "monotonic_dec"

    # pyGAM expects a 2-D design matrix.
    X = xm.reshape(-1, 1)
    try:
        gam = LinearGAM(gam_s(0, constraints=constraint)).fit(X, ym)
    except Exception as e:  # pyGAM raises various errors on degenerate fits.
        gs.warning(_("Monotone GAM fit failed ({}); skipping the GAM curve.").format(e))
        return None

    fitted = np.asarray(gam.predict(X), dtype="float64")
    try:
        band = gam.confidence_intervals(X, width=0.95)
        lower = np.asarray(band[:, 0], dtype="float64")
        upper = np.asarray(band[:, 1], dtype="float64")
    except Exception:
        lower = upper = None

    try:
        pseudo_r2 = float(
            gam.statistics_.get("pseudo_r2", {}).get("explained_deviance", np.nan)
        )
    except Exception:
        pseudo_r2 = float("nan")

    return {
        "fitted": fitted,
        "lower": lower,
        "upper": upper,
        "x": xm,
        "direction": resolved,
        "change": float(fitted[-1] - fitted[0]),
        "pseudo_r2": pseudo_r2,
    }


def fit_trend(
    series,
    trim=0,
    fit_gam_curve=False,
    gam_direction="auto",
    scale=1.0,
    unit_label=None,
):
    """Linear and monotone-GAM regression of the deseasonalized series vs time.

    The regressions are fit on the **deseasonalized observed** series, i.e.
    ``trend + residual`` (equivalently ``observed - seasonal``).

    Uses scipy.stats.linregress, giving slope, intercept, R^2 and the two-sided
    p-value of the slope in one call.

    The fit is always done in index space (x = observation number), so the raw
    slopes are a value change per observation step. ``scale`` converts those
    into a value change per reporting unit (per day/week/month/year, or per
    step), and ``unit_label`` names that unit. The conversion is applied only
    to slope-like quantities (OLS/Theil-Sen slope and their confidence bounds,
    the GAM net change), stored under the ``*_report`` keys; the dimensionless
    statistics (R^2, p-values, Kendall tau) are never scaled. The raw,
    index-space ``slope``/``intercept``/``sen_slope``/``sen_intercept`` keys are
    kept unchanged because the plotted lines are drawn in index space.

    The first and last STL trend points are extrapolated by LOESS from one-sided
    neighbourhoods, making them less reliable. Setting ``trim`` drops that
    many observations from each end before the fit, so the regression is
    computed only over the interior where the estimate is trustworthy. The same
    trim is applied to all three fits (OLS, Theil-Sen and GAM) for consistency.

    The x axis used for the regression keeps the original observation indexing:
    after trimming, the first retained point has x = ``trim`` (not 0). The
    returned ``x_start`` and ``x_stop`` give the inclusive index range the fit
    spans, so the line can be drawn over exactly that range.

    :param pandas.Series series: the deseasonalized observed series
        (trend + residual)
    :param int trim: number of observations to drop from each end before the
        fit. Values < 0 are treated as 0. If trimming would leave fewer than
        two points, the fit falls back to the full (untrimmed) series.
    :param bool fit_gam_curve: also fit a monotone GAM curve (requires pygam).
    :param str gam_direction: 'auto', 'increasing' or 'decreasing'.
    :param float scale: multiplier converting a per-step slope into a per-unit
        slope (from slope_unit_scale()).
    :param str|None unit_label: name of the reporting unit (e.g. 'year').
    :return dict|None: regression results, or None if there are fewer than two
        valid observations even without trimming. The dict keys are spelled out
        in the ``return {...}`` block below; the non-obvious ones are: the raw
        ``slope``/``sen_slope`` etc. are in index space (per observation step),
        while their ``*_report`` counterparts are scaled to the reporting unit;
        ``x_start``/``x_stop`` give the inclusive index range the fit spans (so
        the line can be drawn over exactly that range) and ``trim`` is the
        per-side edge trim actually applied.
    """
    n = len(series)
    x_full = np.arange(n)
    y_full = np.asarray(series.values, dtype="float64")

    trim = max(0, int(trim))
    # Only trim if enough interior points remain for a meaningful regression.
    if trim > 0 and n - 2 * trim >= 2:
        sl = slice(trim, n - trim)
    else:
        if trim > 0:
            gs.warning(
                _(
                    "Edge trim of {t} per side leaves too few points "
                    "({n} total); fitting the trend regression on the full "
                    "series instead."
                ).format(t=trim, n=n)
            )
        sl = slice(0, n)

    x = x_full[sl]
    y = y_full[sl]
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return None
    xm = x[mask]
    ym = y[mask]

    # Ordinary least-squares regression: slope, intercept, R^2, p-value.
    reg = linregress(xm, ym)

    # Robust trend: Theil-Sen slope (median of pairwise slopes)
    ts_slope, ts_intercept, ts_lo, ts_hi = theilslopes(ym, xm)
    mk_tau, mk_pvalue = kendalltau(xm, ym)

    # Optional shape-constrained (monotone) GAM curve.
    gam = None
    if fit_gam_curve:
        gam = fit_gam(xm, ym, gam_direction, float(ts_slope))

    scale = float(scale)
    return {
        "slope": float(reg.slope),
        "intercept": float(reg.intercept),
        "r2": float(reg.rvalue) ** 2,
        "pvalue": float(reg.pvalue),
        "sen_slope": float(ts_slope),
        "sen_intercept": float(ts_intercept),
        "sen_lo": float(ts_lo),
        "sen_hi": float(ts_hi),
        "mk_tau": float(mk_tau),
        "mk_pvalue": float(mk_pvalue),
        "gam": gam,
        "x_start": int(x[0]),
        "x_stop": int(x[-1]),
        "trim": int(sl.start),
        # Reporting conversion: index-space (per-step) slopes scaled to the
        # chosen calendar/step unit. The raw keys above are unchanged so the
        # plotted lines stay in index space.
        "scale": scale,
        "unit_label": unit_label,
        "slope_report": float(reg.slope) * scale,
        "sen_slope_report": float(ts_slope) * scale,
        "sen_lo_report": float(ts_lo) * scale,
        "sen_hi_report": float(ts_hi) * scale,
    }


def write_point_vector(vector, east, north, trend_fit=None):
    """Create a point vector layer at the selected (east, north) location.

    When a trend regression is supplied, the OLS slope, R^2 and p-value, plus
    the robust Theil-Sen slope and the Mann-Kendall tau and p-value, are stored
    as attributes of the single point feature. The slope values are in the
    chosen reporting unit (per day/week/month/year, or per step), named in the
    ``slope_unit`` text column. When a monotone GAM was fit, its net change and
    explained deviance are stored too.

    :param str vector: name of the output point vector layer
    :param float east: easting of the point
    :param float north: northing of the point
    :param dict|None trend_fit: regression as returned by fit_trend()
    """
    if trend_fit is not None:
        gam = trend_fit.get("gam")
        gam_change = gam["change"] if gam else ""
        gam_dev = gam["pseudo_r2"] if gam else ""
        unit_label = trend_fit.get("unit_label") or "step"
        columns = [
            "x double precision",
            "y double precision",
            "cat integer",
            "slope double precision",
            "r2 double precision",
            "pvalue double precision",
            "sen_slope double precision",
            "mk_tau double precision",
            "mk_pvalue double precision",
            "slope_unit varchar(32)",
            "gam_change double precision",
            "gam_deviance double precision",
        ]
        stdin = "{e},{n},1,{s},{r},{p},{ss},{kt},{kp},{u},{gc},{gd}\n".format(
            e=east,
            n=north,
            s=trend_fit.get("slope_report", trend_fit["slope"]),
            r=trend_fit["r2"],
            p=trend_fit["pvalue"],
            ss=trend_fit.get("sen_slope_report", trend_fit.get("sen_slope", "")),
            kt=trend_fit.get("mk_tau", ""),
            kp=trend_fit.get("mk_pvalue", ""),
            u=unit_label,
            gc=gam_change,
            gd=gam_dev,
        )
        kwargs = {"columns": columns, "cat": 3}
    else:
        stdin = "{e},{n}\n".format(e=east, n=north)
        kwargs = {}
    try:
        gs.write_command(
            "v.in.ascii",
            input="-",
            output=vector,
            separator="comma",
            stdin=stdin,
            overwrite=gs.overwrite(),
            **kwargs,
        )
    except CalledModuleError:
        gs.fatal(_("Could not create point vector layer '{}'.").format(vector))
    if trend_fit is not None:
        # The x/y coordinate columns are only needed to import the geometry;
        # drop them so the attribute table holds just the regression stats.
        try:
            gs.run_command("v.db.dropcolumn", map=vector, columns="x,y")
        except CalledModuleError:
            gs.warning(
                _("Could not drop the 'x' and 'y' columns from '{}'.").format(vector)
            )
    gs.message(_("Created point vector layer '{}'.").format(vector))


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


def plot_result(
    result,
    output,
    dpi,
    dimensions,
    east,
    north,
    temporal_type="absolute",
    trend_fit=None,
    show_ols=True,
    show_sen=True,
    show_gam=False,
    show_band=False,
    show_stats=False,
    result2=None,
    trend_fit2=None,
    strds_name=None,
    strds2_name=None,
    same_yscale=False,
    line_color=None,
    line_color2=None,
    fontsize=None,
    line_width=None,
    title=None,
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
    :param object|None result2: STL fit of a second dataset to co-plot.
    :param dict|None trend_fit2: regressions for the second dataset.
    :param str|None strds_name: name of the primary strds (legend).
    :param str|None strds2_name: name of the second strds (legend).
    :param bool same_yscale: share one common y-axis range between the two
        datasets on each panel instead of using a twin right axis.
    :param line_color: series line colour for the first dataset, as a
        matplotlib-ready colour (name or 0-1 RGB/RGBA tuple; the caller converts
        from GRASS colour syntax). Defaults to a blue.
    :param line_color2: series line colour for the second dataset. Defaults to
        an orange.
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
    # A shared y-axis only makes sense with two datasets.
    shared_scale = have_second and same_yscale

    # Unset font size / line width fall back to the Matplotlib/style defaults.
    if fontsize is not None:
        plt.rcParams["font.size"] = fontsize
    legend_fontsize = fontsize * 0.9 if fontsize is not None else "small"
    fig, axes = plt.subplots(4, 1, figsize=dimensions, sharex=True)
    panels = [
        ("Observed", result.observed, result2.observed if have_second else None),
        ("Trend", result.trend, result2.trend if have_second else None),
        ("Seasonal", result.seasonal, result2.seasonal if have_second else None),
        ("Residual", result.resid, result2.resid if have_second else None),
    ]
    # Colour the primary series when a second dataset is present or the user
    # supplied a custom colour; otherwise keep matplotlib's default so a plain
    # single-dataset plot looks unchanged.
    primary_color = color1 if (have_second or line_color) else None

    for ax, (label, comp, comp2) in zip(axes, panels):
        ax.grid(axis="both", color="lightgrey", linewidth=0.3, zorder=0)
        trend_handles = []

        # primary dataset on the left axis
        # ---------------------------------------------------------
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
            trend_handles += draw_trend_lines(
                ax,
                comp,
                trend_fit,
                show_ols,
                show_sen,
                show_gam,
                show_band,
                with_stats=show_stats,
                colors=trend_colors1 if have_second else None,
                label_suffix=" ({})".format(label1) if have_second else "",
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
                trend_handles += draw_trend_lines(
                    ax2,
                    comp2,
                    trend_fit2,
                    show_ols,
                    show_sen,
                    show_gam,
                    show_band,
                    with_stats=show_stats,
                    colors=trend_colors2,
                    label_suffix=" ({})".format(label2),
                )

        if have_second and label == "Trend" and trend_handles:
            ax.legend(
                handles=trend_handles,
                loc="best",
                fontsize=legend_fontsize,
                frameon=False,
            )

        ax.set_ylabel(label)
        ax.margins(x=0.01)

    # A single legend identifying the two datasets, on the Observed panel.
    if have_second:
        observed_ax = axes[0]
        line1 = mpl.lines.Line2D([], [], color=color1, linewidth=1, label=label1)
        line2 = mpl.lines.Line2D([], [], color=color2, linewidth=1, label=label2)
        observed_ax.legend(
            handles=[line1, line2], loc="best", fontsize=legend_fontsize, frameon=False
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


def validate_odd_window(value, name, minimum):
    """Validate an odd-integer LOESS window length, returning the int value.

    :param str|int value: the option value (may be empty/None)
    :param str name: option name, for the error message
    :param int minimum: smallest allowed value
    :return int|None: the validated integer, or None if unset
    """
    if not value:
        return None
    value = int(value)
    if value < minimum or value % 2 == 0:
        gs.fatal(_("'{n}' must be an odd integer >= {m}.").format(n=name, m=minimum))
    return value


def validate_options(options, flags, temporal_type):
    """Validate option values that depend only on user input (and the cheap
    t.info temporal type), so the module fails fast before the potentially
    expensive t.rast.what sampling step.

    Checks performed here:
      * seasonal / trend / low_pass are odd integers >= their minimum
      * the *_jump options are positive integers
      * spline / polynomial interpolation requires 'order'
      * a relative-time 'step' override is a positive integer

    Data-dependent checks (period vs. length, gaps after interpolation, etc.)
    are intentionally left to run later, once the series is available.

    :param dict options: parsed module options
    :param dict flags: parsed module flags (the 'g' flag triggers an up-front
        pygam availability check)
    :param str temporal_type: 'absolute' or 'relative' (from t.info)
    """
    # STL LOESS window lengths: odd integers, each with its own minimum.
    validate_odd_window(options["seasonal"], "seasonal", 7)
    validate_odd_window(options["trend"], "trend", 3)
    validate_odd_window(options["low_pass"], "low_pass", 3)

    # LOESS jump steps must be positive integers.
    for key in ("seasonal_jump", "trend_jump", "low_pass_jump"):
        if options[key] and int(options[key]) < 1:
            gs.fatal(_("'{}' must be a positive integer.").format(key))

    # Spline/polynomial interpolation needs an explicit order.
    if options["interpolation"] in ("spline", "polynomial") and not options["order"]:
        gs.fatal(
            _("The '{}' interpolation method requires the 'order' option.").format(
                options["interpolation"]
            )
        )

    # Relative-time step override, when given, must be a positive integer.
    if temporal_type == "relative" and options["step"]:
        if int(options["step"]) <= 0:
            gs.fatal(_("The 'step' option must be a positive integer."))

    # Line colours, when given, must be valid GRASS colour specs that map to a
    # colour matplotlib understands (a named colour or an R:G:B[:A] triplet).
    import matplotlib.colors as _mcolors

    for key in ("color", "color2"):
        if options.get(key):
            try:
                converted = grass_color_to_mpl(options[key])
                # None means 'none' (no explicit colour) -> acceptable.
                ok = converted is None or _mcolors.is_color_like(converted)
            except ValueError:
                ok = False
            if not ok:
                gs.fatal(
                    _(
                        "'{k}' value '{v}' is not a valid colour. Use a GRASS "
                        "colour name (e.g. 'blue'), an R:G:B triplet with each "
                        "component in 0-255 (e.g. '0:0:255'), or any matplotlib "
                        "colour such as a hex code ('#1f77b4') or 'tab:' name."
                    ).format(k=key, v=options[key])
                )

    # The monotone GAM curve (-g) needs pygam. Check up front so the module
    # fails fast here rather than after the expensive t.rast.what sampling.
    if flags.get("g"):
        if importlib.util.find_spec("pygam") is None:
            gs.fatal(
                _(
                    "The Python package 'pygam' is required for the monotone "
                    "GAM trend curve (flag -g) but is not installed. Install it "
                    "with e.g. 'pip install pygam', or drop the -g flag."
                )
            )


def decompose_and_fit(
    regular,
    period_opt,
    temporal_type,
    tinfo,
    stl_kwargs,
    trend_trim,
    show_ols,
    show_sen,
    show_gam,
    gam_direction,
    frequency=None,
    step=None,
    slope_unit="auto",
    label=None,
):
    """Run STL and the trend regressions on one regularized series, with reporting.

    This bundles the period inference, STL decomposition, edge-trim handling,
    trend regression and the terminal messages so it can be run for one or two
    datasets. When ``label`` is given (i.e. a second dataset is present) the
    messages are prefixed with it so the two analyses can be told apart.

    :param pandas.Series regular: regularized, gap-free series
    :param str period_opt: the period= option value (may be empty)
    :param str temporal_type: 'absolute' or 'relative'
    :param dict tinfo: parsed t.info -g output for this dataset
    :param dict stl_kwargs: keyword arguments forwarded to run_stl()
    :param str trend_trim: the trend_trim= option value
    :param bool show_ols: report the OLS line
    :param bool show_sen: report the Theil-Sen line
    :param bool show_gam: fit/report the monotone GAM curve
    :param str gam_direction: GAM monotonic direction option
    :param str frequency: the frequency= option (absolute time), for the slope
        reporting-unit conversion
    :param str step: the step= option (relative time), for the slope
        reporting-unit conversion
    :param str slope_unit: the slope_unit= option ('auto','step','day',...)
    :param str|None label: dataset name used to prefix messages (or None)

    :return tuple: (result, trend_fit) where result is the STL fit and
        trend_fit is the dict from fit_trend() (or None)
    """
    prefix = "[{}] ".format(label) if label else ""

    period = infer_period(
        regular,
        period_opt,
        temporal_type=temporal_type,
        tinfo=tinfo,
    )
    if period >= len(regular):
        gs.fatal(
            _(
                "{pre}Seasonal period ({p}) must be smaller than the number of "
                "observations ({n}). Use a coarser frequency, more data, or a "
                "smaller period."
            ).format(pre=prefix, p=period, n=len(regular))
        )
    gs.message(
        _("{pre}Running STL decomposition (period={p})...").format(pre=prefix, p=period)
    )
    result = run_stl(series=regular, period=period, **stl_kwargs)

    # Linear regression of the trend component.
    # Optionally trim LOESS endpoints first.
    if trend_trim and trend_trim != "none":
        tw = effective_trend_window(
            period, stl_kwargs.get("seasonal"), stl_kwargs.get("trend")
        )
        trim = int(round(float(trend_trim) * tw))
        gs.message(
            _("{pre}Effective STL trend window: {w} observations.").format(
                pre=prefix, w=tw
            )
        )
        gs.message(
            _(
                "{pre}Trend regression edge trim: {f} x trend window = {t} "
                "observation(s) dropped from each end."
            ).format(pre=prefix, f=trend_trim, t=trim)
        )
    else:
        trim = 0
        gs.message(
            _("{pre}Trend regression edge trim: none (using full series).").format(
                pre=prefix
            )
        )

    # Fit the trend regressions on the deseasonalized observed series
    # (trend + residual)
    deseasonalized = result.trend + result.resid

    # Resolve the slope reporting unit (per day/week/month/year, or per step)
    # so the reported slopes are independent of the resampling frequency.
    # Prefer the regularized series' own frequency (set by resample/asfreq) over
    # the raw frequency= option, which may be empty for already-regular data.
    eff_frequency = frequency
    if temporal_type != "relative":
        series_freq = getattr(regular.index, "freqstr", None)
        if series_freq:
            eff_frequency = series_freq
    scale, unit_label = slope_unit_scale(
        slope_unit=slope_unit,
        temporal_type=temporal_type,
        frequency=eff_frequency,
        step=step,
        tinfo=tinfo,
        n_obs=len(regular),
    )
    gs.message(
        _("{pre}Reporting trend slopes per {u}.").format(pre=prefix, u=unit_label)
    )

    trend_fit = fit_trend(
        deseasonalized,
        trim=trim,
        fit_gam_curve=show_gam,
        gam_direction=gam_direction,
        scale=scale,
        unit_label=unit_label,
    )
    if trend_fit is not None:
        applied = trend_fit.get("trim", 0)
        if trim > 0 and applied != trim:
            # fit_trend fell back (trim too large for the series length).
            gs.warning(
                _(
                    "{pre}Requested edge trim of {req} per side was too large; "
                    "the regression used {act} per side instead."
                ).format(pre=prefix, req=trim, act=applied)
            )
        n_fit = trend_fit["x_stop"] - trend_fit["x_start"] + 1
        gs.message(
            _(
                "{pre}Trend regression fitted on {n} observations "
                "(indices {a}-{b}; {t} trimmed from each end)."
            ).format(
                pre=prefix,
                n=n_fit,
                a=trend_fit["x_start"],
                b=trend_fit["x_stop"],
                t=applied,
            )
        )
        if show_ols:
            gs.message(
                _("{pre}Trend (OLS): slope={s}, R^2={r:.3f}, p={p:.3g}").format(
                    pre=prefix,
                    s=format_slope(trend_fit["slope_report"], unit_label),
                    r=trend_fit["r2"],
                    p=trend_fit["pvalue"],
                )
            )
        if show_sen:
            gs.message(
                _(
                    "{pre}Trend (Theil-Sen / Mann-Kendall): slope={s}, "
                    "tau={t:.3f}, p={p:.3g}"
                ).format(
                    pre=prefix,
                    s=format_slope(trend_fit["sen_slope_report"], unit_label),
                    t=trend_fit["mk_tau"],
                    p=trend_fit["mk_pvalue"],
                )
            )
        if show_gam and trend_fit.get("gam") is not None:
            g = trend_fit["gam"]
            gs.message(
                _(
                    "{pre}Trend (monotone GAM, {d}): net change={c}, "
                    "explained deviance={r:.3f}"
                ).format(
                    pre=prefix,
                    d=g["direction"],
                    c=format_slope(g["change"]),
                    r=g["pseudo_r2"],
                )
            )

    return result, trend_fit


def main(options, flags):
    """Extract a point series from an strds and run an STL decomposition."""

    output = options["output"]
    backend_opt = options["backend"]
    coordinates = options["coordinates"]
    strds = options["strds"]
    strds2 = options["strds2"]
    where = options["where"]
    nprocs = int(options["nprocs"]) if options["nprocs"] else 1
    frequency = options["frequency"]
    interpolation = options["interpolation"]
    order = options["order"]
    step = options["step"]
    period_opt = options["period"]
    seasonal = options["seasonal"]
    trend = options["trend"]
    low_pass = options["low_pass"]
    seasonal_degree = options["seasonal_degree"]
    trend_degree = options["trend_degree"]
    low_pass_degree = options["low_pass_degree"]
    seasonal_jump = options["seasonal_jump"]
    trend_jump = options["trend_jump"]
    low_pass_jump = options["low_pass_jump"]
    trend_trim = options["trend_trim"]
    gam_direction = options["gam_direction"]
    slope_unit = options["slope_unit"]
    csv = options["csv"]
    vector = options["vector"]
    plot_dimensions = options["plot_dimensions"]
    dpi = float(options["dpi"]) if options["dpi"] else 300

    robust = flags["r"]
    show_ols = flags["o"]
    show_sen = flags["s"]
    show_gam = flags["g"]
    show_band = flags["b"]
    show_stats = flags["t"]
    same_yscale = flags["y"]
    line_color = grass_color_to_mpl(options["color"]) if options["color"] else None
    line_color2 = grass_color_to_mpl(options["color2"]) if options["color2"] else None
    fontsize = float(options["fontsize"]) if options["fontsize"] else None
    line_width = float(options["line_width"]) if options["line_width"] else None
    title = options["title"]

    # Select the matplotlib backend: explicit > output-driven default.
    if backend_opt:
        backend = backend_opt
    elif output:
        backend = "Agg"
    else:
        backend = "WXAgg"
    lazy_import_py_modules(backend=backend)
    apply_style(options["style"])

    # Get the point coordinates
    east, north = coords_from_option(coordinates)
    gs.message(_("Using point (east, north) = ({}, {})").format(east, north))

    # Check if the strds exists and read its temporal type.
    try:
        tinfo = gs.parse_command("t.info", flags="g", input=strds)
    except CalledModuleError:
        gs.fatal(_("Space-time raster dataset '{}' not found.").format(strds))
    temporal_type = tinfo.get("temporal_type", "absolute")

    # Validate option-only requirements up front.
    validate_options(options, flags, temporal_type)

    # Build the list of datasets to analyze. The second strds is optional
    datasets = [(strds, tinfo)]
    if strds2:
        try:
            tinfo2 = gs.parse_command("t.info", flags="g", input=strds2)
        except CalledModuleError:
            gs.fatal(_("Space-time raster dataset '{}' not found.").format(strds2))
        temporal_type2 = tinfo2.get("temporal_type", "absolute")
        if temporal_type2 != temporal_type:
            gs.fatal(
                _(
                    "The two datasets have different temporal types "
                    "('{a}' vs '{b}'). Both must be either absolute or "
                    "relative time."
                ).format(a=temporal_type, b=temporal_type2)
            )
        datasets.append((strds2, tinfo2))

    stl_kwargs = {
        "seasonal": seasonal,
        "trend": trend,
        "low_pass": low_pass,
        "seasonal_deg": seasonal_degree,
        "trend_deg": trend_degree,
        "low_pass_deg": low_pass_degree,
        "seasonal_jump": seasonal_jump,
        "trend_jump": trend_jump,
        "low_pass_jump": low_pass_jump,
        "robust": robust,
    }

    # Extract -> regularize -> decompose/fit each dataset. When a second dataset
    # is present, its terminal messages are prefixed with its name.
    results = []
    for index, (ds_name, ds_tinfo) in enumerate(datasets):
        label = (strds2 and ds_name) or None
        if index == 0:
            gs.message(_("Extracting the point time series..."))
        else:
            gs.message(
                _("Extracting the point time series for '{}'...").format(ds_name)
            )
        ds_dates, ds_values = extract_series(
            strds=ds_name,
            east=east,
            north=north,
            where=where,
            nprocs=nprocs,
        )
        ds_series = build_series(ds_dates, ds_values, temporal_type=temporal_type)
        n_valid = int(ds_series.notna().sum())
        gs.message(
            _("Extracted {n} timesteps ({v} non-null).").format(
                n=len(ds_series), v=n_valid
            )
        )
        if n_valid == 0:
            gs.fatal(
                _(
                    "All extracted values are NULL at this point for '{}'; "
                    "nothing to decompose."
                ).format(ds_name)
            )

        gs.message(_("Regularizing the series and interpolating gaps..."))
        ds_regular = regularize(
            series=ds_series,
            frequency=frequency,
            method=interpolation,
            order=order,
            temporal_type=temporal_type,
            step=step,
            tinfo=ds_tinfo,
        )
        ds_result, ds_trend_fit = decompose_and_fit(
            ds_regular,
            period_opt,
            temporal_type,
            ds_tinfo,
            stl_kwargs,
            trend_trim,
            show_ols,
            show_sen,
            show_gam,
            gam_direction,
            frequency=frequency,
            step=step,
            slope_unit=slope_unit,
            label=label,
        )
        results.append((ds_result, ds_trend_fit))

    result, trend_fit = results[0]
    result2, trend_fit2 = results[1] if len(results) > 1 else (None, None)

    # Write CSV if requested
    if csv:
        write_csv(result, csv, temporal_type=temporal_type)

    # Create point vector layer if requested.
    if vector:
        write_point_vector(vector, east, north, trend_fit=trend_fit)

    # Plot (save-by-extension or show).
    gs.message(_("Creating the figure..."))
    if plot_dimensions:
        dimensions = [float(x) for x in plot_dimensions.split(",")]
    else:
        dimensions = [8, 8]
    plot_result(
        result=result,
        output=output,
        dpi=dpi,
        dimensions=dimensions,
        east=east,
        north=north,
        temporal_type=temporal_type,
        trend_fit=trend_fit,
        show_ols=show_ols,
        show_sen=show_sen,
        show_gam=show_gam,
        show_band=show_band,
        show_stats=show_stats,
        result2=result2,
        trend_fit2=trend_fit2,
        strds_name=strds,
        strds2_name=strds2,
        same_yscale=same_yscale,
        line_color=line_color,
        line_color2=line_color2,
        fontsize=fontsize,
        line_width=line_width,
        title=title,
    )


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
