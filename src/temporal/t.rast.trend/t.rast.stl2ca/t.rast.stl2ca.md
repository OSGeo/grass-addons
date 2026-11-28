## DESCRIPTION

t.rast.stl2ca extracts, for every **category** of a raster map or vector map,
the time series of a space-time raster dataset (STRDS), as the mean, median or
other statistic of the pixels in that category. It then carries out a **STL
decomposition** (Seasonal-Trend decomposition using LOESS) on each category's
series and draws every category together on one multi-panel plot comparing the
observed series, *trend*, *seasonal* and *residual* (remainder) components.
Optionally, a robust Theil-Sen trend regression can be fitted to each category's
deseasonalized series and drawn on the trend panel.

The categories can be defined by a categorical raster layer (**raster**), or a
vector map's features grouped by an attribute column
(**map**/**layer**/**column**). This can, for example, be a land-cover raster,
or a vector of administrative units grouped by region name. t.rast.stl2ca
complements *[t.rast.stl](t.rast.stl.md)*, which can instead compare two
*datasets* sampled at one, manually chosen area.

The module supports strds with absolute (calendar-dated) or relative
(integer-stepped) time. Every category's series is regularized onto the same
evenly spaced time axis, and then run through
[statsmodels.tsa.seasonal.STL](https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html).

### Acknowledgement

This tool was developed for the
[Save the tiger! Save the Grasslands! Save the Water!](https://savethetiger.nl/)
project, funded by the Dutch Research Council (NWO) under award
<https://doi.org/10.61686/UYHYF97856>.

### About STL

Environmental time series of e.g., a vegetation index, land surface temperature,
snow cover, or soil moisture, are normally composed of:

- A repeating **seasonal** pattern, e.g. vegetation greening up every spring and
  senescing every autumn;
- A slower **trend**, e.g. a multi-year changes such as recovery after a
  disturbance, or climate change;
- Short-term **residual** variation that is left over once season and trend are
  removed. These include normal day-to-day variation, sensor noise, residual
  cloud contamination, or one-off events such as a fire or a flood.

STL is a procedure that separates these three temporal patterns. It models the
observed value at each date as `observed = trend + seasonal + residual`.

It estimates the trend and seasonal patterns by repeatedly fitting **LOESS**
(LOcally Estimated Scatterplot Smoothing) curves. These are flexible local
regressions that do not assume a fixed global functional shape. STL is robust,
handles long seasonal cycles, and (in its robust variant) can down-weight
outliers such as undetected clouds.

The module can be run with default settings to explore patterns. The minimum
input is the strds and point coordinates. If the maps in the strds are not
regularly spaced, you will need to provide the required frequency as well. For
more information about this parameter and other fine-tune options, see the next
section.

### The categories

Each category is sampled as the mean, median or other statistic of the pixels
that are part of that category. The category can be defined by:

- **raster**: a CELL (integer) raster whose distinct cell values are the
  categories.
- **map** (with **layer** and **column**): a vector map, rasterized and grouped
  by an attribute column. Every feature becomes its own category by default
  (**column=cat**, i.e. not set); giving a different **column** groups features
  that share the same value of that column into one category instead, labelled
  with that value. **column** can be numeric or text.

**raster** and **map** are mutually exclusive; exactly one is required.

By default every distinct category found is processed. **categories** restricts
this to a chosen subset, given as a comma separated list of either the
category's raw value (**raster**) or its label (the **column** value, or the
raster's own category label if it has one). For example *categories=1,3* or
*categories=forest,water*.

The module respects the *current computational region*'s resolution. Set the
region with *[g.region](g.region.md)* before running if needed. A category with
no overlap with the current region, or no non-null data at any registered
timestep, is skipped with a warning.

The per-timestep pixel values within a category are summarized by
**statistic**: `mean` (the default), `median`, `min`, `max` or `percentile`.
`percentile` requires **percentile_value** (0-100). This statistic applies to
every category alike, so they stay comparable; it cannot be set independently
per category. Note that `median` and `percentile` require t.rast.univar's
extended-statistics mode, which can require a lot of memory if used with large
rasters.

The **-d** flag additionally shades a band around each category's Observed
series showing the spread of pixel values at each timestep: ±1 standard
deviation for `mean`, or the interquartile range (25th-75th percentile) for
`median`. It is only valid with `statistic=mean` or `statistic=median`. Gaps
in the band (missing timesteps) are always filled by linear interpolation,
regardless of the **interpolation** option, so a curvature-fitting method
chosen for the series itself cannot overshoot and bulge the band past its true
local range.

A standard deviation or interquartile range estimated from very few pixels is
unreliable and can spike far past the genuine spread, typically on a
near-total-cloud timestep where only a handful of pixels survive. **min_pixels**
guards against this. At timesteps with fewer non-null pixels than this, the band
is left out there too and filled the same way as any other gap.

### Drawing

Every category gets its own color, from **colormap** (a [Matplotlib
colormap](https://matplotlib.org/stable/users/explain/colors/colormaps.html)
name, default `tab10`). Once there are more categories than the chosen colormap
has distinct colors, a continuous colormap (`viridis`) is used instead, sampled
evenly across its range. The reserved value `colormap=raster` instead colors
each category from the **raster** option's own GRASS color table (e.g. one set
with *r.colors*), so the plot reuses the same colors as the classification map
itself. This only applies with **raster**, and a category value with no color
rule in the table falls back to black. The dispersion band (**-d**), seasonal
envelope (**seasonal_envelope**) and Theil-Sen trend line (**-s**) are each
drawn in the category's own color.

### Interactive plot

The **-i** flag writes an interactive HTML plot (using
[Plotly](https://plotly.com/python/), a separate Python package from Matplotlib)
instead of a static image, with the same panels, colours and legend as the
static figure. **output** must then end in `.html`; if **output** is left out,
the plot is opened in a browser tab instead of being shown in a window. The
interactive plot has the following features:

- Click a category's legend entry to highlight it. This will cause the other
  category's lines, across every panel, to fade to a thin grey. You can continue
  to click other entries to highlight several at once. Clicking a highlighted
  entry again removes it from the highlight.
- Dragging across any panel zooms into that time range. Double-click to reset
  the zoom.
- Hovering any panel shows the date and category's value at that point, and
  draws a crosshair through every panel at that date.
- A "Trend statistics" tab in the top-left corner opens a sidebar holding the
  same table **stats_output** writes to a file (see below), whether or not
  **stats_output** is actually given.

**backend**, **dpi**, **plot_dimensions** and **style** are Matplotlib-only and
are ignored for the HTML plot with a warning.

### Absolute vs. relative time

The tool handles both temporal types of strds. For **absolute-time** datasets
the x-axis of the plot is labelled with dates. For **relative-time** datasets
the x-axis is labelled "Time step".

### Regularization

STL requires an evenly spaced, gap-free series. The series is therefore
resampled onto a regular axis, and any gaps are then filled in. Four options
control this:

**frequency** sets the spacing of the regular axis for absolute-time datasets.
It is a [pandas offset
alias](https://pandas.pydata.org/docs/user_guide/timeseries.html#time-span-representation).
Common choices are `D` (daily), `W` (weekly), `MS` (month start), or e.g., `16D`
for a 16-day composite series. For absolute-time datasets that are already
regularly spaced, **frequency** may be omitted, and the spacing is inferred. For
irregular data, you should set it explicitly to fit the desired / intended
spacing.

**step** sets the spacing for relative-time datasets, as an integer in the
dataset's own time unit (**frequency** is ignored for relative-time datasets).
If **step** is omitted, the dataset granularity reported by `t.info` is used,
and the extent of the regular axis is taken from the data. Observations that do
not fall on a grid node are snapped to the nearest node (with a warning), and
two observations landing on the same node are averaged.

**interpolation** chooses how gaps left after resampling are filled. The default
is a `linear` interpolation. If gaps are uneven, you might want to use the
`time` option, which takes into account the actual time distance between
observations. For the other options, `nearest`, `pchip`, `akima`, `cubic`,
`quadratic`, `spline` and `polynomial`, see the manual page of the Pandas
[Series.interpolate](https://pandas.pydata.org/docs/reference/api/pandas.Series.interpolate.html)
function, which this module uses for the gap filling.

Only gaps between observations are filled. Steps before the first and after the
last observation, e.g., when the dataset starts or ends with NULL maps, are left
out, so the analysed series covers the observed period only. The module reports
the number of left-out steps, the number of interpolated steps, and the length
of the longest gap. A warning is given when a gap spans one seasonal period or
more, as the seasonal component over that gap is then interpolated rather than
observed. **max_gap** sets the longest run of consecutive missing
steps that may be interpolated; a longer gap stops the module with the dates of
that gap. By default, gaps of any length are interpolated.

You will normally want to make sure the **frequency** (or **step**) matches the
real sampling of your data. If these are not matching, your data will be
resampled. For example, setting data that is actually 16-day composites to `D`
(daily) will create many interpolated points and smoothen the data series.

### Decomposition (STL)

The decomposition wraps `statsmodels.tsa.seasonal.STL`. Its most important
parameter is **period**, which is tied to the regularized frequency (or, for
relative-time data, the step / granularity). It is the number of observations in
one full seasonal cycle. For example, 12 for monthly data, 23 for a 16-day
composite series (≈ 365 / 16), or 365 for daily data with an annual cycle. If
**period** is not given, it is estimated from the resampled frequency (or, for
relative-time data, the dataset granularity): an annual cycle for daily and
longer steps, and a daily cycle for hourly and shorter steps (e.g., 24 for
hourly data). Set it explicitly whenever you are unsure the inference will be
right, or when your cycle is different.

The remaining STL options fine-tune the LOESS smoothers. For users familiar with
[R's stl()](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/stl.html)
function, many of these parameters are similar or identical, although the
defaults may differ.

**seasonal**: length of the seasonal smoother (odd integer ≥ 7). Smaller values
let the seasonal shape change quickly from cycle to cycle; larger values force a
more stable, near-constant season. The equivalent parameter in R's stl()
function is `s.window`.

**trend**: length of the trend smoother (odd integer). Larger values give a
smoother, stiffer trend that ignores short wiggles; smaller values let the trend
bend more. If left empty, statsmodels derives a default from the period and
seasonal window. The equivalent parameter in R's stl() function is `t.window`.

**low_pass**: length of the low-pass smoother (odd integer ≥ 3). This is an
internal step separating season from trend. The default (the smallest odd number
larger than **period**) is almost always fine. The equivalent parameter in R's
stl() function is `l.window`.

**seasonal_degree**, **trend_degree**, **low_pass_degree**: the degree of the
local polynomial each LOESS uses (0 = locally constant, 1 = locally linear).
statsmodels defaults to 1. R's `stl()` also uses 1 for the trend (`t.degree`)
and low-pass (`l.degree`) smoothers, but 0 for the seasonal smoother
(`s.degree`).

**seasonal_jump**, **trend_jump**, **low_pass_jump**: control the trade-off
between speed and accuracy. The LOESS is evaluated every jump observations and
interpolated in between; 1 (the default) evaluates at every point and is the
most exact.

**-r** (robust flag): turns on robust fitting, which iteratively down-weights
outliers. This is worth enabling when residual cloud or sensor spikes are
distorting the fit.

### Seasonal amplitude envelope

The **seasonal_envelope** option draws a rolling envelope of the seasonal
component on the Seasonal panel: a moving window one seasonal **period**
wide, centered on each point, tracks the local extremes of the seasonal
cycle. It can be used to show a decrease or increase in the amplitude over
time (for example, a vegetation index whose greening/senescence amplitude
strengthens or dampens across years).

The value is the fraction trimmed off each end of the window before taking
the envelope: `seasonal_envelope=0` uses the plain min/max of the window,
while e.g. `seasonal_envelope=0.1` uses its 10th/90th percentile instead,
so that one unusually extreme cycle doesn't dominate the envelope. A window
that doesn't fully fit (the first/last half-period of the series) is left
as a gap rather than computed from a partial window.

### Trend line and statistics

The tool can quantify the long-term change by fitting regressions to the
**deseasonalized observed** series and drawing them on the trend panel. The
deseasonalized series is `trend + residual`, which is equivalent to
`observed - seasonal`.

Three fits are available. The first is an ordinary least-squares (OLS) line,
reported with its **slope** and **R²**. The second is a robust Theil-Sen line
(SciPy's
[theilslopes](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html)),
reported with its slope and a monotonic-trend *p*-value from Kendall's
rank-correlation test (SciPy's
[kendalltau](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kendalltau.html)).
This option is more resistant to outliers and does not assume normal residuals.
The **mk_test** option offers variants that correct for serial autocorrelation,
computed with the [pymannkendall](https://github.com/mmhs013/pyMannKendall)
package:

- `kendall` (default): Kendall's rank correlation test (SciPy), no correction
  for autocorrelation;
- `hamed_rao`: the Hamed–Rao modified test, which inflates the variance of the
  test statistic based on the significant autocorrelation lags of the ranks of
  the detrended series;
- `yue_wang`: the Yue–Wang modified test, a similar variance correction based on
  the autocorrelation of the detrended series;
- `prewhiten`: the test applied to the pre-whitened series, i.e., with the
  lag-1 autocorrelation removed.

The variants only change the Mann-Kendall tau and *p*-value; the Theil-Sen slope
is the same. For these variants, tau is pymannkendall's estimate (the
Mann-Kendall *S* statistic divided by the number of pairs), which for the
pre-whitening variant is computed on the pre-whitened series. It can therefore
differ from the default tau.

The **-s** flag draws the Theil-Sen line on the trend panel; **stats_output**
writes its numbers (slope, Kendall's tau, p-value) to a CSV file, one row per
category, regardless of **-s**.

The slopes are reported as a change per time unit, set with **slope_unit**. The
default, `auto`, picks the largest of day, week, month and year that the series
spans at least three times, so a multi-year series is reported per year. Set
`day`, `week`, `month` or `year` to choose the unit yourself, or `step` to
report the change per observation of the regularized series, i.e., per step of
the chosen **frequency** (absolute series) or **step** (relative series), e.g.,
per 16-day step for a 16D series. For a relative-time series, the calendar units
are only available when its time unit is days, weeks, months or years; otherwise
the slopes are reported per step.

The STL trend LOESS has to **extrapolate** at both ends of the series because,
near the boundaries, it can only use data from one side. The corresponding ends
of the deseasonalized series are therefore the least reliable and can
disproportionately influence the fitted regression. The **trend_trim** option
reduces this edge effect by dropping a portion of each end before fitting. The
trimming amount is specified as a fraction of the effective trend window:

- `none` (default) uses the whole series;
- `0.1` / `0.25` remove only the outermost, most biased points;
- `0.5` removes the entire theoretically-extrapolated zone (about half the trend
  window at each end);
- `1` is the most conservative.

If you see a fitted line being pulled by an upswing or downswing right at the
edge of the plot, increasing **trend_trim** is the appropriate fix.

### Trend breakpoints

A single OLS/Theil-Sen slope over the whole series averages away a real turning
point, such as a rise, a decline, or a renewed rise. The **breakpoints** option
splits the OLS/Theil-Sen fit into separate segments instead: one or more dates
(absolute-time) or time steps (relative-time), each starting a new segment, with
the series' own start and end as the outer boundaries. Each segment is reported
and drawn with its own slope/R²/*p*, labelled by its date (or step) range. Note
that this option is ignored used for The GAM curve (**-g**). Combine
**breakpoints** with matching **vlines** values to also mark them on the plot. A
segment left with too few observations after trimming (fewer than 4) is rejected
with an error naming it.

### Vertical reference lines

The **vlines** option draws one or more dashed vertical reference lines across
every panel, for example to mark a known event (a fire, flood, land-use
change, or similar) against the decomposition. Give one or more dates
(*vlines=2019-08-15*) for absolute-time **strds**, or one or more integer time
steps for relative-time **strds**; separate multiple values with commas
(*vlines=2015-01-01,2019-08-15*). Optional text labels for each line can be
given with **vlines_labels**, in the same order and count as **vlines**
(*vlines_labels=Fire,Flood*); they are shown rotated above the top panel.

### Output

By default the multi-panel plot is shown in an interactive window. If **output**
is given, the plot is instead saved to that file and the image format is taken
from the file extension (`.png`, `.pdf`, `.svg`, ...). See "Interactive plot"
above for the **-i** flag, which writes an HTML plot instead and changes
**output**'s meaning. The rest of this section is about the static image. Plot
appearance is controlled by **dpi** (resolution, default 300) and
**plot_dimensions** (width,height in inches). The **style** option applies a
Matplotlib
[style sheet](https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html)
to the plot, e.g. *style=ggplot*. It also accepts the path to a custom
[.mplstyle file](https://matplotlib.org/stable/tutorials/introductory/customizing.html#defining-your-own-style),
e.g. to set a thinner `axes.linewidth` than any built-in style does.

The **plots** option selects which of the four panels (observed, trend,
seasonal, residual) are drawn. By default all four are shown; list a subset to
leave the others out, for example, *plots=observed,trend* to draw only the
observed series and its trend. At least one panel is required. The Theil-Sen
trend line (**-s**) is only drawn when the trend panel is included. When
**plot_dimensions** is not set, the default figure height scales with the number
of selected panels (about 2 inches each, so the full four-panel figure is 8x8
inches).

The **backend** option selects the matplotlib rendering backend. You rarely need
it: `Agg` is chosen automatically when writing to a file, and `WXAgg` (an
interactive window) when no output file is given. Override it only if your
system needs a different interactive backend (e.g., `TkAgg`, `Qt5Agg`).

**stats_output**, when given, writes the Theil-Sen/Kendall trend statistics
(slope, tau, p-value, the **mk_test** variant, the reporting unit, number of
observations fitted) to a CSV file, one row per category, and one row per
**breakpoints** segment, when given, in addition to the whole-series row. This
is independent of **-s**: the statistics are computed either way, this option
just decides whether they are written out. With **-i**, the same table is also
always shown in the HTML output, in a sidebar opened from the "Trend statistics"
tab (see "Interactive plot" above), whether or not **stats_output** is given.

### Subsetting and performance

The **where** option accepts a temporal WHERE clause (as used by other `t.*`
modules) to restrict the analysis to a subset of timestamps, for example, a
particular range of years. Note that in the interactive plot, you can plot the
whole range and select the range you are interested in in the plot (see above).

The **nprocs** option sets the number of parallel processes
*[t.rast.univar](t.rast.univar.md)* uses for the zonal extraction, which covers
every category in one call. Be careful not to set this higher than the number of CPU cores
available.

The module automatically shrinks the region it samples at to the categories' own
extent first (see "The categories" above), which mostly helps when the
categories occupy only a small part of a much larger current region. But note
that it can still take long time when there are many maps.

## NOTES

This addon requires the following Python packages:

- **pandas** builds the time-indexed series, resamples it onto the regular axis
  (`Series.resample`) and fills gaps (`Series.interpolate`).
- **statsmodels** performs the STL decomposition
  ([statsmodels.tsa.seasonal.STL](https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html)),
  splitting the series into trend, seasonal and residual components.
- **scipy** fits the trend regressions: the OLS line
  ([scipy.stats.linregress](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html)),
  the robust Theil-Sen line
  ([scipy.stats.theilslopes](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html)),
  and the monotonic-trend *p*-value from Kendall's rank correlation
  ([scipy.stats.kendalltau](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kendalltau.html)).
- **pymannkendall** computes the optional autocorrelation-corrected
  Mann-Kendall tests selected with **mk_test** ([pymannkendall](https://github.com/mmhs013/pymannkendall)).
- **numpy** provides the array operations underlying the above, and
  **matplotlib** renders the multi-panel plot.

They are all pip-installable, e.g.

```sh
pip install numpy pandas scipy matplotlib statsmodels
```

If a dependency is missing, the module exits with a message indicating which
package to install. Exception is *pymannkendall*, which is an optional
dependency (`pip install pymannkendall`). It is imported only when **mk_test**
is set to another value than `kendall`, so the rest of the module works without
it.

## EXAMPLES

TODO

## SEE ALSO

*[t.rast.trend](t.rast.trend.md), [t.rast.stl](t.rast.stl.md),
[t.rast.line](t.rast.line.md),
[t.rast.univar](t.rast.univar.md), [v.to.rast](v.to.rast.md),
[r.reclass](r.reclass.md)*

## REFERENCES

- Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I. (1990).
  STL: a seasonal-trend decomposition procedure based on loess. *Journal of
  Official Statistics*, 6, 3–73:
  [STL paper (PDF)](https://www.math.unm.edu/~lil/Stat581/STL.pdf).
- Dasari, N. (2025a). Time Series Forecasting Made Simple (Part 1):
  Decomposition and Baseline Models. *Towards Data Science*
  [Part I article](https://towardsdatascience.com/time-series-forecasting-made-simple-part-1-decomposition-baseline-models).
- Dasari, N. (2025b). Time Series Forecasting Made Simple (Part 2): Customizing
  Baseline Models. *Towards Data Science*
  [Part II article](https://towardsdatascience.com/time-series-forecasting-made-simple-part-2-customizing-baseline-models/).
- Hamed, K. H., & Rao, A. R. (1998). A modified Mann-Kendall trend test for
  autocorrelated data. *Journal of Hydrology*, 204(1–4), 182–196.
- Hussain et al., (2019). pyMannKendall: a python package for non parametric
  Mann Kendall family of trend tests.. Journal of Open Source Software, 4(39),
  1556, <https://doi.org/10.21105/joss.01556>
- Local regression. (2026). In *Wikipedia*
  [Wikipedia local regression article](https://en.wikipedia.org/wiki/Local_regression).
- Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and Statistical
  Modeling with Python. SciPy 2010. <https://doi.org/10.25080/Majora-92bf1922-011>
- statsmodels. (2025). *Statsmodels* (Version 0.14.6) [Python]
  [statsmodels repository](https://github.com/statsmodels/statsmodels/).
- Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T.,
  Cournapeau, D., Burovski, E., Peterson, P., Weckesser, W., Bright, J., Van
  Der Walt, S. J., Brett, M., Wilson, J., Millman, K. J., Mayorov, N.,
  Nelson, A. R. J., Jones, E., Kern, R., Larson, E., … Vázquez-Baeza, Y.
  (2020). SciPy 1.0: Fundamental algorithms for scientific computing in
  Python. Nature Methods, 17(3), 261–272.
  <https://doi.org/10.1038/s41592-019-0686-2>
- Yue, S., & Wang, C. Y. (2004). The Mann-Kendall test modified by effective
  sample size to detect trend in serially correlated hydrological series.
  *Water Resources Management*, 18(3), 201–218.

## AUTHOR

[Paulo van Breugel](https://ecodiv.earth),
[Innovative Biomonitoring](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/)
and
[Climate-robust Landscapes](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
research groups at the [HAS green academy](https://has.nl)
