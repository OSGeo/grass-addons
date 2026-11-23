#!/usr/bin/env python

############################################################################
#
# MODULE:       t.rast.stl2ca
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Extracts the time series of every category of a
#               classification (a CELL raster's own cell values, or a
#               vector map grouped by an attribute column) from the same
#               space-time raster dataset (strds), regularizes each onto an
#               evenly spaced axis, runs an STL decomposition
#               (seasonal / trend / remainder) on each, and plots all
#               categories together on one multi-panel figure.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: STL decomposition (seasonal/trend/remainder) of a strds for every category of a classification raster or vector
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

# %option G_OPT_R_INPUT
# % key: raster
# % required: no
# % label: Categories raster
# % description: CELL raster whose distinct cell values define the categories; each is sampled as its own zone. Mutually exclusive with 'map'.
# % guisection: Input
# %end

# %option G_OPT_V_MAP
# % key: map
# % required: no
# % label: Categories vector map
# % description: Vector map whose features define the categories, grouped by 'column'. Mutually exclusive with 'raster'.
# % guisection: Input
# %end

# %option G_OPT_V_FIELD
# % key: layer
# % guisection: Input
# %end

# %option G_OPT_DB_COLUMN
# % key: column
# % label: Category column
# % description: Attribute column (of 'map', given 'layer') grouping features into categories; features sharing a value become one category, labelled with that value. Defaults to 'cat', i.e. one category per feature. Ignored when 'raster' is used.
# % guisection: Input
# %end

# %option
# % key: categories
# % type: string
# % label: Categories to process
# % description: Category value(s) or label(s) to restrict processing to (comma separated). Unset processes every distinct category found.
# % multiple: yes
# % required: no
# % guisection: Input
# %end

# %option
# % key: statistic
# % type: string
# % label: Pixel aggregation statistic
# % description: Statistic used to summarize the pixels within each category at each timestep. 'mean', 'min' and 'max' use a single, cheap t.rast.univar call. 'median' and 'percentile' are more robust to outlier/contaminated pixels but require t.rast.univar's extended-statistics mode, which sorts all cell values in memory for each map; this is a real memory cost on very large rasters.
# % options: mean,median,min,max,percentile
# % answer: mean
# % required: no
# % guisection: Input
# %end

# %option
# % key: percentile_value
# % type: double
# % label: Percentile to use as the statistic
# % description: Percentile (0-100) summarizing the pixels within each category at each timestep. Only used when 'statistic' is 'percentile'.
# % options: 0-100
# % required: no
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
# % key: s
# % label: Theil-Sen trend line
# % description: Draw the robust Theil-Sen regression line on the Trend panel, in each category's own color. Its slope/Mann-Kendall p-value are always available via 'stats_output' regardless of this flag.
# % guisection: Trend line
# %end

# %option
# % key: slope_unit
# % type: string
# % label: Reporting unit for trend slopes
# % description: Time unit the slopes reported in 'stats_output' are expressed per (value change per unit). 'auto' picks a readable calendar unit (day/week/month/year) from the series span for absolute-time data; 'step' keeps the value change per observation step (per frequency/step). For relative-time data only 'auto' and 'step' apply.
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
# % guisection: Trend line
# %end

# %option
# % key: breakpoints
# % type: string
# % label: Trend regression breakpoints
# % description: Date(s) (absolute-time strds) or time step(s) (relative-time strds) splitting the trend regression into separate segments, e.g. to report the slope before and after a known change rather than one slope that averages over it. Each value starts a new segment; the series' own start and end always count as the outer segment boundaries. Comma separated for multiple breakpoints. 'trend_trim' only trims the series' true start/end, not an interior breakpoint (which is not a LOESS edge). Combine with 'vlines' (same dates/steps) to also mark the breakpoints on the plot.
# % multiple: yes
# % required: no
# % guisection: Trend line
# %end

# %option
# % key: plots
# % type: string
# % label: Panels to include in the figure
# % description: Which decomposition panels to draw, as a comma separated subset of observed, trend, seasonal and residual. Omitted panels are left out of the figure; at least one panel is required. The Theil-Sen trend line is only drawn when the trend panel is included.
# % options: observed,trend,seasonal,residual
# % multiple: yes
# % answer: observed,trend,seasonal,residual
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: colormap
# % type: string
# % label: Category colormap
# % description: Matplotlib colormap assigning each category its own color. Falls back to sampling the continuous 'viridis' colormap once there are more categories than the chosen colormap has distinct colors.
# % answer: tab10
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: style
# % type: string
# % label: Matplotlib style
# % description: Name of a built-in Matplotlib style (see https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html), or the path to a custom .mplstyle file (see https://matplotlib.org/stable/tutorials/introductory/customizing.html#defining-your-own-style).
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: fontsize
# % type: double
# % label: Font size
# % description: Base font size of plot text. Defaults to the Matplotlib/style default.
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: line_width
# % type: double
# % label: Line width
# % description: Width of the series lines. Defaults to the Matplotlib default.
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: title
# % type: string
# % label: Plot title
# % description: The title of the plot. If left empty, no title is drawn.
# % required: no
# % guisection: Plotting
# %end

# %flag
# % key: d
# % label: Show pixel-value spread band
# % description: Shade a band around each category's Observed series showing the spread of pixel values within it at each timestep: +/-1 standard deviation for the 'mean' statistic, or the interquartile range (25th-75th percentile) for the 'median' statistic. Only valid with 'statistic=mean'/'statistic=median'.
# % guisection: Plotting
# %end

# %option
# % key: min_pixels
# % type: integer
# % label: Minimum pixel count for the spread band
# % description: At timesteps where fewer than this many non-null pixels contributed to a category's statistic, the spread band (-d) is left out and interpolated like any other gap, instead of plotting it. A standard deviation or interquartile range estimated from very few pixels is unreliable and can spike far beyond the genuine spread, most visibly on near-total-cloud timesteps where only a handful of pixels survive. Only meaningful with -d.
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: seasonal_envelope
# % type: string
# % label: Seasonal amplitude envelope percentile
# % description: Draw a rolling envelope of the seasonal component (a centered window one seasonal period wide) on the Seasonal panel, showing how the seasonal amplitude changes over time. The value is the fraction trimmed from each end of the window before taking the envelope, e.g. '0.1' uses the 10th/90th percentile instead of the min/max, to avoid outliers dominating the envelope; '0' uses the plain min/max. Unset disables the envelope.
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: vlines
# % type: string
# % label: Vertical reference line date(s)
# % description: Date(s) (absolute-time strds, e.g. '2019-08-15') or time step(s) (relative-time strds, integer) at which to draw a dashed vertical reference line across all panels, e.g. to mark a known event. Comma separated for multiple lines.
# % multiple: yes
# % required: no
# % guisection: Plotting
# %end

# %option
# % key: vlines_labels
# % type: string
# % label: Vertical reference line label(s)
# % description: Optional label(s) for the 'vlines' dates, in the same order. When given, the number of labels must match the number of 'vlines' values. Shown rotated above the top panel.
# % multiple: yes
# % required: no
# % guisection: Plotting
# %end

# %flag
# % key: i
# % label: Interactive HTML plot
# % description: Write an interactive Plotly HTML plot instead of a static image. 'output' must then end in '.html' (or be omitted, opening the plot in a browser tab instead). 'backend', 'dpi', 'plot_dimensions' and 'style' do not apply here and are ignored. Click a category's legend entry to highlight it (click more entries to highlight several; click them again to go back to all categories shown normally); drag across any panel to zoom into a time range (all panels zoom together, since 'plots' still chooses which ones are drawn).
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % required: no
# % label: Name of output plot file
# % description: Output image file. The format is taken from the extension (e.g. .png, .pdf, .svg; .html with '-i'). If omitted, the plot is shown in an interactive window (a browser tab with '-i').
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

# %option G_OPT_F_OUTPUT
# % key: stats_output
# % required: no
# % label: Name of output trend-statistics CSV file
# % description: Writes the Theil-Sen/Mann-Kendall trend statistics (slope, tau, p-value) to this CSV file, one row per category (one row per 'breakpoints' segment too, when given). If omitted, these statistics are not written anywhere.
# % guisection: Output
# %end

# %option G_OPT_M_NPROCS
# % description: Number of parallel processes, forwarded to t.rast.univar's zonal extraction.
# %end

# %option G_OPT_T_WHERE
# %end

# %rules
# % exclusive: raster, map
# % required: raster, map
# % requires: min_pixels, -d
# % requires: vlines_labels, vlines
# %end


import atexit
import sys

import grass.script as gs
from grass.exceptions import CalledModuleError
from grass.script.utils import set_path

if not callable(globals().get("_")):
    from gettext import gettext as _

# extract.py/trend.py/plot.py: this module's own library files (see the
# ETCFILES entry in the Makefile), originally split out of t.rast.stl --
# this addon keeps its own copy since each GRASS addon is installed
# independently. set_path() finds them whether this script is run from its
# installed location or straight from the source tree. Each library file
# leaves its own numpy/pandas/matplotlib/statsmodels/scipy names as None at
# import time (set below, by lazy_import_py_modules(), once GRASS has
# parsed the command line) so a plain module scan (--help, g.extension)
# never needs the scientific stack installed.
set_path("t.rast.stl2ca")
import extract  # noqa: E402
import trend  # noqa: E402
import plot  # noqa: E402
import interactive  # noqa: E402
from extract import (  # noqa: E402
    clean_dirs,
    clean_rasters,
    validate_category_raster,
    validate_vector,
    shrink_region_to_raster,
    shrink_region_to_vector,
    vector_category_raster,
    discover_categories,
    filter_categories,
    extract_zonal_series_multi,
    build_series,
    regularize,
)
from trend import decompose_and_fit, validate_odd_window, write_trend_stats_csv  # noqa: E402
from plot import apply_style, plot_result, parse_vlines  # noqa: E402
from interactive import plot_interactive  # noqa: E402


def cleanup():
    """Remove temporary directories and rasters registered during the run."""
    for path in clean_dirs:
        gs.try_rmdir(path)
    if clean_rasters:
        # vector_category_raster() can register a reclass raster alongside
        # the base map it was built from, and g.remove refuses to remove a
        # base map while a reclass of it still exists -- regardless of the
        # order the two names are given in one call. Two passes clear it:
        # the first removes the reclass map(s), unblocking the base map(s)
        # for the second (a g.remove of an already-removed name is a
        # harmless no-op warning).
        for _ in range(2):
            gs.run_command(
                "g.remove", flags="f", type="raster", name=clean_rasters, quiet=True
            )


def lazy_import_py_modules(backend="WXAgg"):
    """Lazy import of the third-party scientific stack.

    Imports numpy/pandas/statsmodels/scipy/matplotlib once the command line
    has been parsed, and hands each to the library module(s) that use it --
    extract.py/trend.py/plot.py each leave the name as None at import time
    (see their module docstrings) until this runs. This is what keeps a
    plain module scan (--help, g.extension) from ever needing the
    scientific stack installed, now that it lives across four files instead
    of one.

    :param str backend: matplotlib backend to activate before importing pyplot
    """
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
        from statsmodels.tsa.seasonal import STL
    except ModuleNotFoundError:
        gs.fatal(
            _(
                "The Python package 'statsmodels' is required for the STL "
                "decomposition but is not installed. Install it with e.g. "
                "'pip install statsmodels'."
            )
        )

    try:
        from scipy.stats import kendalltau, linregress, theilslopes
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

    extract.np = np
    extract.pd = pd
    trend.np = np
    trend.pd = pd
    trend.STL = STL
    trend.linregress = linregress
    trend.theilslopes = theilslopes
    trend.kendalltau = kendalltau
    plot.np = np
    plot.pd = pd
    plot.mpl = mpl
    plot.plt = plt


def lazy_import_plotly():
    """Lazy import of Plotly, needed only for the '-i' (interactive HTML)
    output mode -- kept separate from lazy_import_py_modules() so an
    ordinary Matplotlib run never requires Plotly to be installed.
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ModuleNotFoundError:
        gs.fatal(
            _(
                "The Python package 'plotly' is required for the '-i' "
                "(interactive HTML) output but is not installed. Install "
                "it with e.g. 'pip install plotly'."
            )
        )

    interactive.go = go
    interactive.make_subplots = make_subplots


def validate_options(options, flags, temporal_type):
    """Validate option values that depend only on user input (and the cheap
    t.info temporal type), so the module fails fast before the potentially
    expensive t.rast.univar sampling step.

    Checks performed here:
      * seasonal / trend / low_pass are odd integers >= their minimum
      * the *_jump options are positive integers
      * spline / polynomial interpolation requires 'order'
      * a relative-time 'step' override is a positive integer
      * an absolute-time 'frequency' is a valid pandas offset alias
      * statistic=percentile requires percentile_value
      * the -d (dispersion band) flag only applies to statistic=mean/median
      * min_pixels, when given, is a positive integer
      * with -i, output (if given) ends in '.html'; warn about any
        Matplotlib-only option/flag that has nothing to do there

    Data-dependent checks (period vs. length, gaps after interpolation, etc.)
    are intentionally left to run later, once the series is available.

    :param dict options: parsed module options
    :param dict flags: parsed module flags
    :param str temporal_type: 'absolute' or 'relative' (from t.info)
    """
    statistic = options["statistic"]
    if statistic == "percentile" and not options["percentile_value"]:
        gs.fatal(
            _(
                "The 'percentile_value' option is required when 'statistic' is 'percentile'."
            )
        )
    if flags["d"] and statistic not in ("mean", "median"):
        gs.fatal(
            _(
                "The '-d' flag (pixel-value spread band) is only meaningful "
                "with 'statistic=mean' or 'statistic=median'."
            )
        )
    if options["min_pixels"] and int(options["min_pixels"]) < 1:
        gs.fatal(_("The 'min_pixels' option must be a positive integer."))

    # Interactive (-i) HTML output: 'output' (if given) must be an .html
    # path, and the Matplotlib-only options/flags have nothing to do there.
    if flags["i"]:
        if options["output"] and not options["output"].lower().endswith(".html"):
            gs.fatal(_("The 'output' file must end in '.html' when '-i' is set."))
        ignored = [
            name
            for name, value in (
                ("backend", options["backend"]),
                ("plot_dimensions", options["plot_dimensions"]),
                ("style", options["style"]),
            )
            if value
        ]
        if ignored:
            gs.warning(
                _("Ignored with '-i' (interactive HTML output): {}.").format(
                    ", ".join(ignored)
                )
            )

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

    # At least one panel must be kept in the figure.
    if not [p for p in options["plots"].split(",") if p]:
        gs.fatal(
            _(
                "At least one panel must be selected in the 'plots' option "
                "(observed, trend, seasonal and/or residual)."
            )
        )

    # Relative-time step override, when given, must be a positive integer.
    if temporal_type == "relative" and options["step"]:
        if int(options["step"]) <= 0:
            gs.fatal(_("The 'step' option must be a positive integer."))

    # Absolute-time 'frequency', when given, must be a pandas offset alias
    # (a unit, optionally with a multiplier), e.g. 'D', 'W', 'MS', '16D',
    # '5YS'. A bare number has no unit and pandas rejects it with an opaque
    # message. The below will catch it and give a clear message instead.
    if temporal_type == "absolute" and options["frequency"]:
        try:
            # lazy_import_py_modules() (called before this) has already set
            # extract.pd; validate_options() itself has no reason to import
            # pandas again just for this one check.
            extract.pd.tseries.frequencies.to_offset(options["frequency"])
        except (ValueError, TypeError):
            gs.fatal(
                _(
                    "The 'frequency' value '{v}' is not a valid pandas offset "
                    "alias. It needs a time unit, optionally with a leading "
                    "multiplier, e.g. 'D' (day), 'W' (week), 'MS' (month "
                    "start), '16D' (16 days), 'YS' or '5YS' (year start). A "
                    "bare number is not accepted."
                ).format(v=options["frequency"])
            )


def resolve_category_raster(options):
    """Resolve the raster=/map=+layer=+column= option group into a
    categories raster and the categories to process.

    :param dict options: parsed module options
    :return tuple: (zone_raster, categories) where categories is a list of
        (int value, str label) tuples in ascending value order, restricted
        to 'categories=' when given
    """
    raster = options["raster"]
    vector = options["map"]

    # Shrink the computational region to the categories' own extent before
    # building the zone raster and sampling the strds (see
    # shrink_region_to_raster()/shrink_region_to_vector() in extract.py):
    # this only reduces how much v.to.rast/t.rast.univar have to sweep, it
    # never changes a result. use_temp_region() is process-local and
    # restores itself when the process exits, so the user's own region is
    # never touched.
    gs.use_temp_region()

    if raster:
        zone_raster = validate_category_raster(raster)
        shrink_region_to_raster(zone_raster)
        gs.message(_("Using the categories of raster '{}'.").format(raster))
    else:
        vector_full = validate_vector(vector)
        layer = options["layer"]
        column = options["column"] or "cat"
        shrink_region_to_vector(vector_full)
        zone_raster = vector_category_raster(vector_full, layer, column)
        gs.message(
            _("Using vector '{v}' grouped by column '{c}' (layer {l}).").format(
                v=vector, c=column, l=layer
            )
        )

    categories = discover_categories(zone_raster)
    categories = filter_categories(categories, options["categories"])
    gs.message(
        _("Processing {n} category/categories: {labels}.").format(
            n=len(categories), labels=", ".join(label for _value, label in categories)
        )
    )
    return zone_raster, categories


def main(options, flags):
    """Extract one series per category from one strds and plot their STL
    decompositions together."""

    output = options["output"]
    backend_opt = options["backend"]
    statistic = options["statistic"]
    percentile_value = (
        float(options["percentile_value"]) if options["percentile_value"] else None
    )
    strds = options["strds"]
    where = options["where"]
    nprocs = int(options["nprocs"]) if options["nprocs"] else 1
    frequency = options["frequency"]
    interpolation = options["interpolation"]
    order = options["order"]
    step = options["step"]
    period_opt = options["period"]
    seasonal = options["seasonal"]
    trend_window = options["trend"]
    low_pass = options["low_pass"]
    seasonal_degree = options["seasonal_degree"]
    trend_degree = options["trend_degree"]
    low_pass_degree = options["low_pass_degree"]
    seasonal_jump = options["seasonal_jump"]
    trend_jump = options["trend_jump"]
    low_pass_jump = options["low_pass_jump"]
    trend_trim = options["trend_trim"]
    breakpoints_opt = options["breakpoints"]
    slope_unit = options["slope_unit"]
    plot_dimensions = options["plot_dimensions"]
    plots = [p for p in options["plots"].split(",") if p] if options["plots"] else []
    dpi = float(options["dpi"]) if options["dpi"] else 300
    colormap = options["colormap"]
    stats_output = options["stats_output"]
    envelope_percentile = None
    if options["seasonal_envelope"]:
        envelope_percentile = float(options["seasonal_envelope"])
        if not 0 <= envelope_percentile < 0.5:
            gs.fatal(_("The 'seasonal_envelope' option must be >= 0 and < 0.5."))

    robust = flags["r"]
    show_sen = flags["s"]
    show_dispersion = flags["d"]
    min_pixels = int(options["min_pixels"]) if options["min_pixels"] else None
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
    if flags["i"]:
        lazy_import_plotly()
    apply_style(options["style"])

    if colormap not in plot.plt.colormaps():
        gs.fatal(_("'{}' is not a known Matplotlib colormap.").format(colormap))

    # Check if the strds exists and read its temporal type.
    try:
        tinfo = gs.parse_command("t.info", flags="g", input=strds)
    except CalledModuleError:
        gs.fatal(_("Space-time raster dataset '{}' not found.").format(strds))
    temporal_type = tinfo.get("temporal_type", "absolute")

    # Validate option-only requirements up front.
    validate_options(options, flags, temporal_type)

    # Vertical reference lines (dates for absolute time, time steps for
    # relative time), parsed here (after the temporal type is known) so a bad
    # value is caught before the expensive sampling step below.
    vlines = parse_vlines(options["vlines"], options["vlines_labels"], temporal_type)

    stl_kwargs = {
        "seasonal": seasonal,
        "trend": trend_window,
        "low_pass": low_pass,
        "seasonal_deg": seasonal_degree,
        "trend_deg": trend_degree,
        "low_pass_deg": low_pass_degree,
        "seasonal_jump": seasonal_jump,
        "trend_jump": trend_jump,
        "low_pass_jump": low_pass_jump,
        "robust": robust,
    }

    zone_raster, category_list = resolve_category_raster(options)

    gs.message(_("Extracting the zonal time series for all categories..."))
    extracted = extract_zonal_series_multi(
        strds=strds,
        zone_raster=zone_raster,
        where=where,
        statistic=statistic,
        nprocs=nprocs,
        want_dispersion=show_dispersion,
        percentile_value=percentile_value,
    )

    # Extract -> regularize -> decompose/fit each category. Each category
    # that comes back empty (no overlap with the strds, or all-null) is
    # skipped with a warning rather than aborting the whole run, since the
    # other categories may well still be usable.
    categories = []
    for value, label in category_list:
        if value not in extracted:
            gs.warning(
                _("No data extracted for category '{}'; skipping.").format(label)
            )
            continue
        ds_dates, ds_values, ds_lower, ds_upper, ds_pixel_counts = extracted[value]

        ds_series = build_series(ds_dates, ds_values, temporal_type=temporal_type)
        n_valid = int(ds_series.notna().sum())
        gs.message(
            _("[{d}] Extracted {n} timesteps ({v} non-null).").format(
                d=label, n=len(ds_series), v=n_valid
            )
        )
        if n_valid == 0:
            gs.warning(
                _("All extracted values are NULL for category '{}'; skipping.").format(
                    label
                )
            )
            continue

        gs.message(
            _("[{d}] Regularizing the series and interpolating gaps...").format(d=label)
        )
        ds_regular = regularize(
            series=ds_series,
            frequency=frequency,
            method=interpolation,
            order=order,
            temporal_type=temporal_type,
            step=step,
            tinfo=tinfo,
        )

        # The dispersion band (if any) is observed-panel annotation only; it
        # is regularized onto the same grid as the series but never goes
        # through decompose_and_fit()/STL.
        ds_band_lower = ds_band_upper = None
        if ds_lower is not None:
            ds_lower_series = build_series(
                ds_dates, ds_lower, temporal_type=temporal_type
            )
            ds_upper_series = build_series(
                ds_dates, ds_upper, temporal_type=temporal_type
            )
            if min_pixels is not None and ds_pixel_counts is not None:
                # A spread computed from very few pixels is a poor estimate
                # and can spike far past the genuine spread -- typically a
                # near-total-cloud timestep where only a handful of pixels
                # survive -- even though the mean/median itself looks normal.
                ds_count_series = build_series(
                    ds_dates, ds_pixel_counts, temporal_type=temporal_type
                )
                low_count_dates = ds_count_series < min_pixels
                n_low_count = int(low_count_dates.sum())
                if n_low_count:
                    gs.message(
                        _(
                            "[{d}] Spread band left out at {n} timestep(s) with "
                            "fewer than {m} non-null pixels."
                        ).format(d=label, n=n_low_count, m=min_pixels)
                    )
                    ds_lower_series = ds_lower_series.mask(low_count_dates)
                    ds_upper_series = ds_upper_series.mask(low_count_dates)
            # Always interpolated linearly, regardless of 'interpolation': a
            # curvature-fitting method (quadratic, cubic, spline...) can
            # overshoot past either neighbour when bridging a gap, which for
            # a dispersion band means manufacturing a bulge wider than the
            # genuine spread on either side. Linear is bounded by its two
            # neighbours and cannot do that.
            ds_band_lower = regularize(
                series=ds_lower_series,
                frequency=frequency,
                method="linear",
                order=None,
                temporal_type=temporal_type,
                step=step,
                tinfo=tinfo,
                report=False,
            )
            ds_band_upper = regularize(
                series=ds_upper_series,
                frequency=frequency,
                method="linear",
                order=None,
                temporal_type=temporal_type,
                step=step,
                tinfo=tinfo,
                report=False,
            )

        (
            ds_result,
            ds_trend_fit,
            ds_trend_fit_segments,
            ds_envelope_lower,
            ds_envelope_upper,
        ) = decompose_and_fit(
            ds_regular,
            period_opt,
            temporal_type,
            tinfo,
            stl_kwargs,
            trend_trim,
            False,  # show_ols: dropped from this addon's interface
            show_sen,
            False,  # show_gam: not exposed in this addon's interface
            None,  # gam_direction: unused when show_gam is False
            frequency=frequency,
            step=step,
            slope_unit=slope_unit,
            label=label,
            envelope_percentile=envelope_percentile,
            breakpoints_opt=breakpoints_opt,
        )
        categories.append(
            {
                "label": label,
                "result": ds_result,
                "trend_fit": ds_trend_fit,
                "trend_fit_segments": ds_trend_fit_segments,
                "band_lower": ds_band_lower,
                "band_upper": ds_band_upper,
                "envelope_lower": ds_envelope_lower,
                "envelope_upper": ds_envelope_upper,
            }
        )

    if not categories:
        gs.fatal(_("No category had usable data; nothing to plot."))

    # Plot: interactive HTML (-i) or the static Matplotlib figure
    # (save-by-extension or show).
    gs.message(_("Creating the figure..."))
    if flags["i"]:
        plot_interactive(
            categories=categories,
            output=output,
            temporal_type=temporal_type,
            plots=plots,
            colormap=colormap,
            title=title,
            line_width=line_width,
            fontsize=fontsize,
            show_sen=show_sen,
            show_band=show_dispersion,
            vlines=vlines,
        )
    else:
        if plot_dimensions:
            dimensions = [float(x) for x in plot_dimensions.split(",")]
        else:
            # Default height scales with the number of panels (2 inches each),
            # so the full four-panel figure stays 8x8 while smaller selections
            # are not stretched vertically.
            dimensions = [8, 2 * len(plots)]
        plot_result(
            categories=categories,
            output=output,
            dpi=dpi,
            dimensions=dimensions,
            temporal_type=temporal_type,
            show_sen=show_sen,
            show_band=show_dispersion,
            line_width=line_width,
            fontsize=fontsize,
            title=title,
            plots=plots,
            colormap=colormap,
            vlines=vlines,
        )

    if stats_output:
        write_trend_stats_csv(categories, stats_output)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
