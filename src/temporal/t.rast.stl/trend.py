############################################################################
#
# MODULE:       t.rast.stl (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      STL decomposition and trend-regression helpers for
#               t.rast.stl: period/window inference, running statsmodels
#               STL, the OLS/Theil-Sen/monotone-GAM trend fits and their
#               reporting-unit conversion, and the CSV/vector output
#               writers.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""STL decomposition, trend regression and their output for t.rast.stl.

np/pd/STL/linregress/theilslopes/kendalltau are set by
t.rast.stl.lazy_import_py_modules() -- after GRASS parses the command line
-- rather than imported here, so a plain module scan (--help, g.extension)
never needs numpy/pandas/statsmodels/scipy installed.
"""

import grass.script as gs
from grass.exceptions import CalledModuleError

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by t.rast.stl.lazy_import_py_modules() before any function below runs.
np = None
pd = None
STL = None
linregress = None
theilslopes = None
kendalltau = None


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


def effective_low_pass_window(period, low_pass):
    """Return the low-pass LOESS window length statsmodels actually uses.

    When the user sets ``low_pass`` explicitly, that value is used.
    Otherwise statsmodels defaults to the smallest odd integer greater than
    ``period`` -- not exposed on the fitted STL object, same as the trend
    window in effective_trend_window() above.

    :param int period: seasonal period
    :param low_pass: user low_pass window or falsy for the statsmodels default
    :return int: the effective (odd) low-pass window length
    """
    if low_pass:
        return int(low_pass)
    win = period + 1
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


def write_csv(
    result,
    csv_path,
    temporal_type="absolute",
    band_lower=None,
    band_upper=None,
    statistic=None,
    envelope_lower=None,
    envelope_upper=None,
):
    """Write the decomposition components to a CSV file.

    When a dispersion band is given (zone mode with the -d flag), it is
    added as extra columns named for what they actually are: 'sd' for the
    mean statistic's +/-1 standard deviation half-width, or
    'first_quartile'/'third_quartile' for the median statistic's IQR bounds.
    When a seasonal envelope is given (the seasonal_envelope= option), it is
    added as 'seasonal_lower'/'seasonal_upper' columns.

    :param dict|None band_lower: regularized lower-band Series, or None
    :param dict|None band_upper: regularized upper-band Series, or None
    :param str|None statistic: 'mean' or 'median' (selects the column
        naming for the band); ignored when no band is given
    :param pandas.Series|None envelope_lower: rolling envelope lower bound of
        the seasonal component, or None
    :param pandas.Series|None envelope_upper: rolling envelope upper bound of
        the seasonal component, or None
    """
    columns = {
        "observed": result.observed,
        "trend": result.trend,
        "seasonal": result.seasonal,
        "residual": result.resid,
    }
    if band_lower is not None and band_upper is not None:
        if statistic == "mean":
            columns["sd"] = result.observed - band_lower
        else:
            columns["first_quartile"] = band_lower
            columns["third_quartile"] = band_upper
    if envelope_lower is not None and envelope_upper is not None:
        columns["seasonal_lower"] = envelope_lower
        columns["seasonal_upper"] = envelope_upper
    df = pd.DataFrame(columns)
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
    start=0,
    stop=None,
    left_trim=0,
    right_trim=0,
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

    ``start``/``stop`` (Python slice convention: ``start`` inclusive, ``stop``
    exclusive) select which window of ``series`` to fit over -- the whole
    series by default. This is what lets decompose_and_fit() fit one segment
    at a time for the breakpoints= option: each call passes that segment's
    own (start, stop).

    The first and last STL trend points of the *whole series* are extrapolated
    by LOESS from one-sided neighbourhoods, making them less reliable; an
    interior breakpoint is not such an edge. ``left_trim``/``right_trim`` drop
    that many observations from the start/end of the window before the fit,
    so the regression is computed only over the interior where the estimate
    is trustworthy -- decompose_and_fit() therefore only ever passes a
    non-zero trim on the side of a window that is also the true start/end of
    the series. The same trim is applied to all three fits (OLS, Theil-Sen
    and GAM) for consistency.

    The x axis used for the regression keeps the original observation indexing:
    after trimming, the first retained point has x = ``start + left_trim``
    (not 0). The returned ``x_start`` and ``x_stop`` give the inclusive index
    range the fit spans, so the line can be drawn over exactly that range.

    :param pandas.Series series: the deseasonalized observed series
        (trend + residual)
    :param int start: first index (inclusive) of the window to fit over.
    :param int|None stop: index one past the last point of the window
        (Python slice convention); None fits to the end of the series.
    :param int left_trim: observations to drop from the start of the window
        before fitting. Values < 0 are treated as 0. If trimming would leave
        fewer than two points, the fit falls back to the untrimmed window.
    :param int right_trim: observations to drop from the end of the window
        before fitting, same fallback as left_trim.
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
        left-side edge trim actually applied.
    """
    n = len(series)
    if stop is None:
        stop = n
    x_full = np.arange(n)
    y_full = np.asarray(series.values, dtype="float64")

    left_trim = max(0, int(left_trim))
    right_trim = max(0, int(right_trim))
    trimmed_start = start + left_trim
    trimmed_stop = stop - right_trim
    # Only trim if enough interior points remain for a meaningful regression.
    if (left_trim or right_trim) and trimmed_stop - trimmed_start >= 2:
        sl = slice(trimmed_start, trimmed_stop)
    else:
        if left_trim or right_trim:
            gs.warning(
                _(
                    "Edge trim of {l}/{r} (left/right) leaves too few points "
                    "in a window of {n}; fitting the trend regression on the "
                    "full window instead."
                ).format(l=left_trim, r=right_trim, n=stop - start)
            )
        sl = slice(start, stop)

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
        "trim": int(sl.start - start),
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


# Below this many observations a linregress/theilslopes fit is numerically
# degenerate (2 points always give a "perfect" R^2 = 1, since a line always
# passes exactly through 2 points) rather than a meaningful regression, so a
# breakpoints= segment shorter than this is rejected instead of silently
# reported.
MIN_SEGMENT_OBS = 4


def resolve_breakpoints(breakpoints_opt, series_index, temporal_type):
    """Resolve the breakpoints= option into sorted integer positions.

    Each value is parsed the same way as vlines= (a date for absolute time,
    an integer time step for relative time), then snapped forward to the
    next position on the regularized series' own index -- the series has
    already been resampled onto a regular grid, so a breakpoint between two
    grid nodes has nowhere exact to go. A value that snaps to the series'
    very first position is dropped (it is not a real breakpoint: the series
    start is already the first segment's boundary).

    :param str breakpoints_opt: the breakpoints= option value (may be empty)
    :param pandas.Index series_index: the regularized (deseasonalized trend)
        series' index
    :param str temporal_type: 'absolute' or 'relative'
    :return list: sorted, de-duplicated breakpoint positions, each in
        (0, len(series_index) - 1]; empty if the option was empty
    """
    if not breakpoints_opt:
        return []
    raw_values = [v.strip() for v in breakpoints_opt.split(",") if v.strip()]
    positions = []
    for value in raw_values:
        if temporal_type == "relative":
            try:
                target = int(value)
            except ValueError:
                gs.fatal(
                    _(
                        "Could not parse 'breakpoints' value '{}' as an "
                        "integer time step."
                    ).format(value)
                )
        else:
            try:
                target = pd.Timestamp(value)
            except (ValueError, TypeError):
                gs.fatal(
                    _("Could not parse 'breakpoints' value '{}' as a date.").format(
                        value
                    )
                )
        pos = int(series_index.searchsorted(target))
        pos = min(max(pos, 0), len(series_index) - 1)
        snapped = series_index[pos]
        if snapped != target:
            gs.message(
                _(
                    "'breakpoints' value '{given}' is not on the regular "
                    "series grid; using the nearest one, {snapped}."
                ).format(given=value, snapped=snapped)
            )
        positions.append(pos)

    positions = sorted(set(positions))
    return [p for p in positions if p > 0]


def build_segments(n, positions):
    """Turn sorted breakpoint positions into (start, stop) index windows.

    Each breakpoint starts a new segment, so segments are contiguous and
    non-overlapping, e.g. ``positions=[80, 200]`` with ``n=400`` gives
    ``[(0, 80), (80, 200), (200, 400)]`` (Python slice convention: start
    inclusive, stop exclusive).

    :param int n: length of the series
    :param list positions: sorted, de-duplicated breakpoint positions, each
        in (0, n)
    :return list: (start, stop) index windows, in order
    """
    bounds = [0] + list(positions) + [n]
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


def format_segment_label(series_index, start, stop, temporal_type):
    """Format a segment's date/step range for a legend/terminal label.

    :param series_index: the deseasonalized series' index
    :param int start: first index (inclusive) of the segment
    :param int stop: index one past the segment's last point (Python slice
        convention)
    :param str temporal_type: 'absolute' or 'relative'
    :return str: e.g. " (2016-01-01..2020-06-15)" or " (0..84)", ready to
        use as a label_suffix
    """
    first = series_index[start]
    last = series_index[stop - 1]
    if temporal_type == "relative":
        return " ({}..{})".format(first, last)
    return " ({}..{})".format(pd.Timestamp(first).date(), pd.Timestamp(last).date())


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
    envelope_percentile=None,
    breakpoints_opt=None,
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
    :param float|None envelope_percentile: also compute the seasonal
        amplitude envelope (a centered rolling window one period wide over
        the seasonal component), for the seasonal_envelope= option. The
        value is the fraction trimmed from each end of the window, e.g. 0.1
        for the 10th/90th percentile, or 0 for the plain min/max. None
        disables the envelope.
    :param str|None breakpoints_opt: the breakpoints= option value (may be
        empty/None). When given, OLS/Theil-Sen are fit separately on each
        segment between breakpoints instead of once over the whole series;
        the monotone GAM curve, if requested, is still fit on the whole
        series (it is not meant to be forced through artificial kinks).

    :return tuple: (result, trend_fit, trend_fit_segments, envelope_lower,
        envelope_upper) where result is the STL fit, trend_fit is the
        whole-series fit_trend() dict (or None) -- always computed, since
        write_csv()/write_point_vector() and the GAM curve use it regardless
        of breakpoints_opt -- trend_fit_segments is a list of (fit_trend()
        dict, label) pairs, one per segment, or None when breakpoints_opt
        was not given, and envelope_lower/envelope_upper are the rolling
        envelope of the seasonal component (or None, None when
        envelope_percentile is None)
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

    # Report the STL smoother windows the user left unset: statsmodels picks
    # its own defaults for them internally, but doesn't expose what it chose
    # on the fitted result, so this is the only way to show it.
    if not stl_kwargs.get("seasonal"):
        gs.message(
            _("{pre}Using the default STL seasonal window of {w} observations.").format(
                pre=prefix, w=7
            )
        )
    tw = effective_trend_window(period, stl_kwargs.get("seasonal"), stl_kwargs.get("trend"))
    if not stl_kwargs.get("trend"):
        gs.message(
            _("{pre}Estimated STL trend window: {w} observations.").format(
                pre=prefix, w=tw
            )
        )
    if not stl_kwargs.get("low_pass"):
        lw = effective_low_pass_window(period, stl_kwargs.get("low_pass"))
        gs.message(
            _("{pre}Estimated STL low-pass window: {w} observations.").format(
                pre=prefix, w=lw
            )
        )

    # Linear regression of the trend component.
    # Optionally trim LOESS endpoints first.
    if trend_trim and trend_trim != "none":
        trim = int(round(float(trend_trim) * tw))
        gs.message(
            _(
                "{pre}Trend regression edge trim: {f} x trend window ({w} "
                "observations) = {t} observation(s) dropped from each end."
            ).format(pre=prefix, f=trend_trim, w=tw, t=trim)
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

    # breakpoints=: fit OLS/Theil-Sen separately on each segment instead of
    # once over the whole series. Only the true start/end of the series get
    # the LOESS edge trim; an interior breakpoint is not a LOESS edge.
    n = len(deseasonalized)
    breakpoint_positions = resolve_breakpoints(
        breakpoints_opt, deseasonalized.index, temporal_type
    )
    trend_fit_segments = None
    if breakpoint_positions:
        trend_fit_segments = []
        for seg_start, seg_stop in build_segments(n, breakpoint_positions):
            seg_label = format_segment_label(
                deseasonalized.index, seg_start, seg_stop, temporal_type
            )
            seg_fit = fit_trend(
                deseasonalized,
                start=seg_start,
                stop=seg_stop,
                left_trim=trim if seg_start == 0 else 0,
                right_trim=trim if seg_stop == n else 0,
                fit_gam_curve=False,
                scale=scale,
                unit_label=unit_label,
            )
            n_seg = seg_fit["x_stop"] - seg_fit["x_start"] + 1 if seg_fit else 0
            if seg_fit is None or n_seg < MIN_SEGMENT_OBS:
                gs.fatal(
                    _(
                        "{pre}Segment{label} has only {n} observation(s) after "
                        "trimming, below the minimum of {m} for a meaningful "
                        "regression. Choose fewer or more widely spaced "
                        "'breakpoints'."
                    ).format(pre=prefix, label=seg_label, n=n_seg, m=MIN_SEGMENT_OBS)
                )
            trend_fit_segments.append((seg_fit, seg_label))
            gs.message(
                _(
                    "{pre}Trend segment{label}: fitted on {n} observations "
                    "(indices {a}-{b})."
                ).format(
                    pre=prefix,
                    label=seg_label,
                    n=n_seg,
                    a=seg_fit["x_start"],
                    b=seg_fit["x_stop"],
                )
            )
            if show_ols:
                gs.message(
                    _("{pre}Trend{label} (OLS): slope={s}, R^2={r:.3f}, p={p:.3g}").format(
                        pre=prefix,
                        label=seg_label,
                        s=format_slope(seg_fit["slope_report"], unit_label),
                        r=seg_fit["r2"],
                        p=seg_fit["pvalue"],
                    )
                )
            if show_sen:
                gs.message(
                    _(
                        "{pre}Trend{label} (Theil-Sen / Mann-Kendall): slope={s}, "
                        "tau={t:.3f}, p={p:.3g}"
                    ).format(
                        pre=prefix,
                        label=seg_label,
                        s=format_slope(seg_fit["sen_slope_report"], unit_label),
                        t=seg_fit["mk_tau"],
                        p=seg_fit["mk_pvalue"],
                    )
                )

    # Whole-series fit: always computed, regardless of breakpoints_opt --
    # write_csv()/write_point_vector() report it unconditionally, and the
    # GAM curve (if requested) is only ever fit over the whole series.
    trend_fit = fit_trend(
        deseasonalized,
        start=0,
        stop=n,
        left_trim=trim,
        right_trim=trim,
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
        # With breakpoints_opt, the segment OLS/Sen lines above replace the
        # whole-series ones on the plot and in the terminal, so these would
        # just repeat (now-superseded) numbers already printed.
        if show_ols and not trend_fit_segments:
            gs.message(
                _("{pre}Trend (OLS): slope={s}, R^2={r:.3f}, p={p:.3g}").format(
                    pre=prefix,
                    s=format_slope(trend_fit["slope_report"], unit_label),
                    r=trend_fit["r2"],
                    p=trend_fit["pvalue"],
                )
            )
        if show_sen and not trend_fit_segments:
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

    # Seasonal amplitude envelope: a rolling envelope of the seasonal
    # component over a window one period wide, showing how the amplitude of
    # the seasonal cycle itself changes over time. envelope_percentile trims
    # that fraction off each end of the window instead of taking the plain
    # min/max, so a handful of outlier years don't dominate the envelope;
    # quantile(0)/quantile(1) are exactly the min/max, so 0 reproduces that
    # plain envelope. Centered, so it needs a full window on both sides; the
    # first/last half-period are left as gaps (NaN) rather than computed
    # from a partial, less meaningful window.
    envelope_lower = envelope_upper = None
    if envelope_percentile is not None:
        roll = result.seasonal.rolling(window=period, center=True)
        envelope_upper = roll.quantile(1 - envelope_percentile)
        envelope_lower = roll.quantile(envelope_percentile)

    return result, trend_fit, trend_fit_segments, envelope_lower, envelope_upper
