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
# % description: STL decomposition (seasonal/trend/remainder) of a single point's time series from a space-time raster dataset
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
# % guisection: Trend regression
# %end

# %flag
# % key: s
# % label: Theil-Sen trend line
# % description: Add the robust Theil-Sen regression line (slope and Mann-Kendall p-value) to the trend panel.
# % guisection: Trend regression
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

# %option G_OPT_M_NPROCS
# %end

# %option G_OPT_T_WHERE
# %end


import atexit
import os
import sys

import grass.script as gs
from grass.exceptions import CalledModuleError


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
        from scipy.stats import linregress as _linregress
        from scipy.stats import theilslopes as _theilslopes
        from scipy.stats import kendalltau as _kendalltau

        linregress = _linregress
        theilslopes = _theilslopes
        kendalltau = _kendalltau
    except ModuleNotFoundError:
        gs.fatal(
            _(
                "The Python package 'scipy' is required for the trend "
                "regression but is not installed. Install it with e.g. "
                "'pip install scipy'."
            )
        )

    try:
        import matplotlib as mpl

        mpl.use(backend)
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is required but not installed. Please install it."))


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
    # directory and the assembled result are written to an file in that same
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
        # the last observation to avoids a non-existing trailing node.
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
        "M": 12,
        "MS": 12,
        "ME": 12,
        "Q": 4,
        "QS": 4,
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

    def _odd_window(value, name, minimum):
        """Validate an odd-integer LOESS window length."""
        value = int(value)
        if value < minimum or value % 2 == 0:
            gs.fatal(
                _("'{n}' must be an odd integer >= {m}.").format(n=name, m=minimum)
            )
        return value

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

    if seasonal:
        kwargs["seasonal"] = _odd_window(seasonal, "seasonal", 7)
    if trend:
        kwargs["trend"] = _odd_window(trend, "trend", 3)
    if low_pass:
        kwargs["low_pass"] = _odd_window(low_pass, "low_pass", 3)

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

    Thee trend-window-based edge trim has to know the resolved trend window,
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


def format_slope(value):
    """Format a slope as a plain decimal (no scientific notation).

    This picks enough decimal places to show four significant
    figures of the value.

    :param float value: slope value
    :return str: fixed-point string, e.g. '0.00006489'
    """
    if value == 0 or not np.isfinite(value):
        return "{:.4f}".format(value)
    # Decimals needed so the first significant digit plus 3 more are shown.
    import math

    leading = int(math.floor(math.log10(abs(value))))
    decimals = max(4, 3 - leading)
    return "{:.{d}f}".format(value, d=decimals)


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


def fit_trend(trend, trim=0):
    """Linear regression of the STL trend component against time.

    Uses scipy.stats.linregress, giving slope, intercept, R^2 and the two-sided
    p-value of the slope in one call.

    The first and last STL trend points are extrapolated by LOESS from one-sided
    neighbourhoods, making them the les reliable. Setting ``trim`` drops that
    many observations from each end before the fit, so the regression is
    computed only over the interior where the trend estimate is trustworthy.

    The x axis used for the regression keeps the original observation indexing:
    after trimming, the first retained point has x = ``trim`` (not 0). The
    returned ``x_start`` and ``x_stop`` give the inclusive index range the fit
    spans, so the line can be drawn over exactly that range.

    :param pandas.Series trend: the STL trend component
    :param int trim: number of observations to drop from each end before the
        fit. Values < 0 are treated as 0. If trimming would leave fewer than
        two points, the fit falls back to the full (untrimmed) series.
    :return dict|None: regression results, or None if there are fewer than two
        valid observations even without trimming. Keys: 'slope', 'intercept',
        'r2', 'pvalue' (ordinary least squares); 'sen_slope', 'sen_intercept',
        'sen_lo', 'sen_hi' (Theil-Sen slope and its confidence interval);
        'mk_tau', 'mk_pvalue' (Mann-Kendall / Kendall tau monotonic-trend
        test); and 'x_start', 'x_stop', 'trim' (the fitted index range).
    """
    n = len(trend)
    x_full = np.arange(n)
    y_full = np.asarray(trend.values, dtype="float64")

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
        "x_start": int(x[0]),
        "x_stop": int(x[-1]),
        "trim": int(sl.start),
    }


def write_point_vector(vector, east, north, trend_fit=None):
    """Create a point vector layer at the selected (east, north) location.

    When a trend regression is supplied, the OLS slope, intercept, R^2 and
    p-value, plus the robust Theil-Sen slope and the Mann-Kendall tau and
    p-value, are stored as attributes of the single point feature.

    :param str vector: name of the output point vector layer
    :param float east: easting of the point
    :param float north: northing of the point
    :param dict|None trend_fit: regression as returned by fit_trend()
    """
    if trend_fit is not None:
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
        ]
        stdin = "{e},{n},1,{s},{r},{p},{ss},{kt},{kp}\n".format(
            e=east,
            n=north,
            s=trend_fit["slope"],
            r=trend_fit["r2"],
            p=trend_fit["pvalue"],
            ss=trend_fit.get("sen_slope", ""),
            kt=trend_fit.get("mk_tau", ""),
            kp=trend_fit.get("mk_pvalue", ""),
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
):
    """Build the multi-panel STL plot, in the style of R's plot(stl(...)).

    Saves to file when output is given (format from extension), otherwise
    shows an interactive window.

    :param dict|None trend_fit: precomputed linear regression of the trend
        component, as returned by fit_trend(); when given, the requested
        regression line(s) and their statistics are drawn on the Trend panel.
    :param bool show_ols: draw the ordinary least-squares (OLS) trend line.
    :param bool show_sen: draw the robust Theil-Sen trend line.
    """
    fig, axes = plt.subplots(4, 1, figsize=dimensions, sharex=True)
    panels = [
        ("Observed", result.observed),
        ("Trend", result.trend),
        ("Seasonal", result.seasonal),
        ("Residual", result.resid),
    ]
    for ax, (label, comp) in zip(axes, panels):
        ax.grid(axis="both", color="lightgrey", linewidth=0.3, zorder=0)
        if label == "Residual":
            ax.axhline(0, color="grey", linewidth=0.8, zorder=1)
            ax.plot(comp.index, comp.values, marker="o", markersize=2, linestyle="none")
        else:
            ax.plot(comp.index, comp.values, linewidth=1)
        if label == "Trend" and trend_fit is not None:
            # Draw the precomputed trend lines over exactly the index range the
            # regressions were fitted on (the trimmed interior, when edge
            # trimming is enabled), using the same x origin as fit_trend.
            x0 = trend_fit.get("x_start", 0)
            x1 = trend_fit.get("x_stop", len(comp) - 1)
            x = np.arange(x0, x1 + 1)
            idx = comp.index[x0 : x1 + 1]

            drew_line = False
            # Ordinary least-squares line (slope + R^2 reported).
            if show_ols:
                ols = trend_fit["slope"] * x + trend_fit["intercept"]
                ax.plot(
                    idx,
                    ols,
                    color="tab:red",
                    linestyle="--",
                    linewidth=1,
                    label="OLS (slope = {}, $R^2$ = {:.3f})".format(
                        format_slope(trend_fit["slope"]), trend_fit["r2"]
                    ),
                )
                drew_line = True
            # Robust Theil-Sen line (slope + Mann-Kendall p reported).
            if show_sen and "sen_slope" in trend_fit:
                sen = trend_fit["sen_slope"] * x + trend_fit["sen_intercept"]
                ax.plot(
                    idx,
                    sen,
                    color="tab:green",
                    linestyle="-.",
                    linewidth=1,
                    label="Theil-Sen (slope = {}, MK p = {:.3f})".format(
                        format_slope(trend_fit["sen_slope"]), trend_fit["mk_pvalue"]
                    ),
                )
                drew_line = True
            if drew_line:
                ax.legend(loc="best", fontsize="small", frameon=False)
        ax.set_ylabel(label)
        ax.margins(x=0.01)
    axes[-1].set_xlabel("Time step" if temporal_type == "relative" else "Date")
    fig.align_ylabels(axes)

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


def main(options, flags):
    """Extract a point series from an strds and run an STL decomposition."""

    output = options["output"]
    backend_opt = options["backend"]
    coordinates = options["coordinates"]
    strds = options["strds"]
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
    csv = options["csv"]
    vector = options["vector"]
    plot_dimensions = options["plot_dimensions"]
    dpi = float(options["dpi"]) if options["dpi"] else 300

    robust = flags["r"]
    show_ols = flags["o"]
    show_sen = flags["s"]

    # Select the matplotlib backend: explicit > output-driven default.
    if backend_opt:
        backend = backend_opt
    elif output:
        backend = "Agg"
    else:
        backend = "WXAgg"
    lazy_import_py_modules(backend=backend)

    # Get the point coordinates
    east, north = coords_from_option(coordinates)
    gs.message(_("Using point (east, north) = ({}, {})").format(east, north))

    # Check if the strds exists and read its temporal type.
    try:
        tinfo = gs.parse_command("t.info", flags="g", input=strds)
    except CalledModuleError:
        gs.fatal(_("Space-time raster dataset '{}' not found.").format(strds))
    temporal_type = tinfo.get("temporal_type", "absolute")

    # Extract the data (date, value) series at the point.
    gs.message(_("Extracting the point time series..."))
    dates, values = extract_series(
        strds=strds,
        east=east,
        north=north,
        where=where,
        nprocs=nprocs,
    )
    series = build_series(dates, values, temporal_type=temporal_type)
    n_valid = int(series.notna().sum())
    gs.message(
        _("Extracted {n} timesteps ({v} non-null).").format(n=len(series), v=n_valid)
    )
    if n_valid == 0:
        gs.fatal(
            _("All extracted values are NULL at this point; nothing to decompose.")
        )

    # Regularize onto an even axis and interpolate gaps.
    gs.message(_("Regularizing the series and interpolating gaps..."))
    regular = regularize(
        series=series,
        frequency=frequency,
        method=interpolation,
        order=order,
        temporal_type=temporal_type,
        step=step,
        tinfo=tinfo,
    )

    # Decompose the time series.
    period = infer_period(
        regular,
        period_opt,
        temporal_type=temporal_type,
        tinfo=tinfo,
    )
    if period >= len(regular):
        gs.fatal(
            _(
                "Seasonal period ({p}) must be smaller than the number of "
                "observations ({n}). Use a coarser frequency, more data, or a "
                "smaller period."
            ).format(p=period, n=len(regular))
        )
    gs.message(_("Running STL decomposition (period={})...").format(period))
    result = run_stl(
        series=regular,
        period=period,
        seasonal=seasonal,
        trend=trend,
        low_pass=low_pass,
        seasonal_deg=seasonal_degree,
        trend_deg=trend_degree,
        low_pass_deg=low_pass_degree,
        seasonal_jump=seasonal_jump,
        trend_jump=trend_jump,
        low_pass_jump=low_pass_jump,
        robust=robust,
    )

    # Linear regression of the trend component.
    # Optionally trim LOESS endpoints first.
    if trend_trim and trend_trim != "none":
        tw = effective_trend_window(period, seasonal, trend)
        trim = int(round(float(trend_trim) * tw))
        gs.message(_("Effective STL trend window: {w} observations.").format(w=tw))
        gs.message(
            _(
                "Trend regression edge trim: {f} x trend window = {t} "
                "observation(s) dropped from each end."
            ).format(f=trend_trim, t=trim)
        )
    else:
        trim = 0
        gs.message(_("Trend regression edge trim: none (using full series)."))
    trend_fit = fit_trend(result.trend, trim=trim)
    if trend_fit is not None:
        applied = trend_fit.get("trim", 0)
        if trim > 0 and applied != trim:
            # fit_trend fell back (trim too large for the series length).
            gs.warning(
                _(
                    "Requested edge trim of {req} per side was too large; "
                    "the regression used {act} per side instead."
                ).format(req=trim, act=applied)
            )
        n_fit = trend_fit["x_stop"] - trend_fit["x_start"] + 1
        gs.message(
            _(
                "Trend regression fitted on {n} observations "
                "(indices {a}-{b}; {t} trimmed from each end)."
            ).format(n=n_fit, a=trend_fit["x_start"], b=trend_fit["x_stop"], t=applied)
        )
        if show_ols:
            gs.message(
                _("Trend (OLS): slope={s}, R^2={r:.3f}, p={p:.3g}").format(
                    s=format_slope(trend_fit["slope"]),
                    r=trend_fit["r2"],
                    p=trend_fit["pvalue"],
                )
            )
        if show_sen:
            gs.message(
                _(
                    "Trend (Theil-Sen / Mann-Kendall): slope={s}, tau={t:.3f}, p={p:.3g}"
                ).format(
                    s=format_slope(trend_fit["sen_slope"]),
                    t=trend_fit["mk_tau"],
                    p=trend_fit["mk_pvalue"],
                )
            )

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
    )


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
