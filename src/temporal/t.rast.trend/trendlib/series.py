############################################################################
#
# MODULE:       t.rast.trend / trendlib (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Data-extraction and regularization helpers shared by the
#               t.rast.trend tools: sampling a strds at a point/zone/raster,
#               parsing the t.rast.univar/t.rast.what output, the
#               temporal-outlier filter, and resampling the series onto a
#               regular, gap-free axis.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""Data extraction, sampling-area preparation, outlier filtering and
regularization, shared by t.rast.stl, t.rast.stl2ca and t.rast.breakpoint.

np/pd are set by each driver script's lazy_import_py_modules() -- after
GRASS parses the command line -- rather than imported here, so a plain
module scan (--help, g.extension) never needs numpy/pandas installed.
"""

import os

import grass.script as gs
from grass.exceptions import CalledModuleError

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by the driver script's lazy_import_py_modules() before any function
# below runs.
np = None
pd = None

# Temporary dirs/rasters created during extraction, removed by the driver
# script's cleanup() at exit.
clean_dirs = []
clean_rasters = []


def resolve_nprocs(value):
    """Turn the nprocs= option value into a number of processes.

    As GRASS's G_OPT_M_NPROCS: a positive number is used as is, 0 means all
    available cores, and a negative number all cores but that many (at
    least 1). Since GRASS 8.5 the option's default is 0, which t.rast.what
    does not accept (it divides by nprocs), so it has to be resolved here.
    GRASS 8.6 provides this as
    grass.script.utils.resolve_nprocs(); the fallback reproduces it for
    older versions.

    :param str value: the nprocs= option value (may be empty)
    :return int: number of processes, at least 1
    """
    if not value:
        return 1
    try:
        from grass.script.utils import resolve_nprocs as grass_resolve_nprocs
    except ImportError:
        n = int(value)
        if n > 0:
            return n
        return max(1, (os.cpu_count() or 1) + n)
    return grass_resolve_nprocs(value)


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


def validate_zone(zone):
    """Check that the zone= vector map exists.

    :param str zone: name of the vector map (as given on the command line)
    """
    found = gs.find_file(name=zone, element="vector")
    if not found.get("fullname"):
        gs.fatal(_("Vector map '{}' not found.").format(zone))


def make_zone_raster(zone):
    """Rasterize zone= into a single-category zones raster for t.rast.univar.

    All features in the vector, of any geometry type (point, line or area),
    are burned to the same category value (1), so the strds is sampled as one
    pooled zone regardless of how many features the vector has. The raster is
    registered in ``clean_rasters`` for removal by cleanup().

    Feature-type and emptiness are not checked beforehand: if the vector has
    nothing that rasterizes into the current region (e.g. it falls outside
    it), that shows up here as zero non-null cells and is fatal.

    :param str zone: name of the input vector map
    :return str: name of the created zones raster
    """
    zone_raster = gs.tempname(12)
    try:
        gs.run_command(
            "v.to.rast",
            input=zone,
            output=zone_raster,
            use="val",
            value=1,
            quiet=True,
        )
    except CalledModuleError:
        gs.fatal(_("Could not rasterize the zone vector map '{}'.").format(zone))
    clean_rasters.append(zone_raster)

    stats = gs.parse_command("r.univar", flags="g", map=zone_raster)
    if int(stats.get("n", 0)) == 0:
        gs.fatal(
            _(
                "The zone vector map '{}' has no features that fall within "
                "the current computational region; nothing to sample."
            ).format(zone)
        )
    return zone_raster


def zone_bbox_center(zone):
    """Center of the zone vector map's bounding box, for messages/tagging only.

    This is not used for sampling (the actual sampling area is the rasterized
    zone, see make_zone_raster()); it is just a representative (east, north)
    location for terminal messages and the optional 'vector' output.

    :param str zone: name of the vector map
    :return tuple: (east, north) as floats
    """
    info = gs.parse_command("v.info", flags="g", map=zone)
    east = (float(info["east"]) + float(info["west"])) / 2.0
    north = (float(info["north"]) + float(info["south"])) / 2.0
    return (east, north)


def validate_raster(raster):
    """Check that the raster= map defining the sampling area exists.

    :param str raster: name of the raster map (as given on the command line)
    """
    found = gs.find_file(name=raster, element="cell")
    if not found.get("fullname"):
        gs.fatal(_("Raster map '{}' not found.").format(raster))


def make_raster_zone(raster):
    """Turn raster= into a single-category zones raster for t.rast.univar.

    Every non-null cell of raster= is burned to the same category value (1),
    regardless of its actual value, so the strds is sampled as one pooled
    zone over all non-null cells. The raster is registered in
    ``clean_rasters`` for removal by cleanup().

    Only isnull() is evaluated, so this costs the same for CELL, FCELL or
    DCELL input; the cell type of raster= does not affect performance here.

    :param str raster: name of the input raster map
    :return str: name of the created zones raster
    """
    zone_raster = gs.tempname(12)
    try:
        gs.run_command(
            "r.mapcalc",
            expression=f"{zone_raster} = if(isnull({raster}), null(), 1)",
            quiet=True,
        )
    except CalledModuleError:
        gs.fatal(
            _("Could not derive the sampling area from raster '{}'.").format(raster)
        )
    clean_rasters.append(zone_raster)

    stats = gs.parse_command("r.univar", flags="g", map=zone_raster)
    if int(stats.get("n", 0)) == 0:
        gs.fatal(
            _(
                "Raster '{}' has no non-null cells within the current "
                "computational region; nothing to sample."
            ).format(raster)
        )
    return zone_raster


def raster_bbox_center(raster):
    """Center of the raster= map's bounding box, for messages/tagging only.

    This is not used for sampling (the actual sampling area is the non-null
    cells, see make_raster_zone()); it is just a representative (east,
    north) location for terminal messages and the optional 'vector' output.

    :param str raster: name of the raster map
    :return tuple: (east, north) as floats
    """
    info = gs.parse_command("r.info", flags="g", map=raster)
    east = (float(info["east"]) + float(info["west"])) / 2.0
    north = (float(info["north"]) + float(info["south"])) / 2.0
    return (east, north)


def sampling_location(coordinates, zone, raster, statistic):
    """Set up the sampling location from the coordinates/zone/raster options.

    Exactly one of the three is expected to be set (the tools' %rules
    enforce that). A zone or raster is turned into a single-category zones
    raster for t.rast.univar; a point is sampled directly.

    :param str coordinates: the coordinates= option value ("east,north")
    :param str zone: the zone= option value (vector map), or empty
    :param str raster: the raster= option value, or empty
    :param str statistic: the statistic= option value, for the message only
    :return tuple: (zone_raster, east, north); zone_raster is None for a
        point, and (east, north) is the point itself or, for a zone/raster,
        its bounding-box center (for messages and vector output only)
    """
    if zone:
        validate_zone(zone)
        zone_raster = make_zone_raster(zone)
        east, north = zone_bbox_center(zone)
        gs.message(
            _(
                "Using zone '{}' ({} statistic; bbox center for tagging: "
                "east={}, north={})."
            ).format(zone, statistic, east, north)
        )
    elif raster:
        validate_raster(raster)
        zone_raster = make_raster_zone(raster)
        east, north = raster_bbox_center(raster)
        gs.message(
            _(
                "Using raster '{}' non-null cells ({} statistic; bbox center "
                "for tagging: east={}, north={})."
            ).format(raster, statistic, east, north)
        )
    else:
        zone_raster = None
        east, north = coords_from_option(coordinates)
        gs.message(_("Using point (east, north) = ({}, {})").format(east, north))
    return zone_raster, east, north


def find_column(header, name):
    """Return the index of a column named ``name`` in a pipe-table header.

    Used by the t.rast.what/t.rast.univar parsers so they locate their
    columns by name rather than by (version-dependent) position.

    :param list header: header row, already split on '|'
    :param str name: column name to look up
    :return int|None: column index, or None if not present
    """
    try:
        return header.index(name)
    except ValueError:
        return None


def parse_zonal_token(token):
    """Parse one t.rast.univar cell value, mapping null/NaN tokens to None.

    t.rast.univar reports an all-null timestep (e.g. no valid pixels in the
    zone) as 'nan' or '-nan' rather than the '*'/'None' tokens t.rast.what
    uses, so those are treated as missing here too.

    :param str token: raw cell value
    :return float|None: the parsed value, or None if missing/unparseable
    """
    token = token.strip()
    if token.lower() in ("", "*", "none", "nan", "-nan"):
        return None
    try:
        return float(token)
    except ValueError:
        return None


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
    start_idx = find_column(header, "start")
    if start_idx is None:
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


def percentile_column_name(value):
    """Build the t.rast.univar column name for a percentile value.

    Mirrors the string transform GRASS core's own
    grass.temporal.univar_statistics uses to name percentile columns
    (e.g. 90 -> 'percentile_90', 95.5 -> 'percentile_95_5'), so this stays
    coupled to that naming and needs updating if it ever changes there.

    :param float value: percentile value (0-100)
    :return str: the matching t.rast.univar column name
    """
    token = str(float(value)).rstrip("0").rstrip(".").replace(".", "_")
    return f"percentile_{token}"


def extract_zonal_series(
    strds, zone_raster, where, statistic, nprocs, want_dispersion, percentile_value=None
):
    """Extract a (date, value) series pooled over a zone from an strds.

    A single t.rast.univar call (zones=zone_raster) covers every registered
    timestep; with a single-category zones raster this yields exactly one
    row per timestep, the zonal equivalent of extract_series()'s one point
    per timestep.

    'mean', 'min' and 'max' use the plain (non-extended) statistics, which
    already include the standard deviation and the min/max columns. 'median'
    and 'percentile' require t.rast.univar's extended-statistics mode (-e);
    for 'median' this also yields the first/third quartiles used for the
    dispersion band, at no extra cost. Extended statistics sort all cell
    values in memory per map, a real cost on very large rasters.

    :param str strds: name of the input space-time raster dataset
    :param str zone_raster: name of the (single-category) zones raster
    :param str where: optional t.* WHERE clause to subset maps
    :param str statistic: 'mean', 'median', 'min', 'max' or 'percentile'
    :param int nprocs: number of parallel processes for t.rast.univar
    :param bool want_dispersion: also return the lower/upper dispersion band
        (mean +/- stddev, or the first/third quartile for median); only
        valid with statistic 'mean' or 'median'
    :param float|None percentile_value: percentile (0-100) to use when
        statistic is 'percentile'; ignored otherwise

    :return tuple: (dates, values, lower, upper, pixel_counts) where
        lower/upper/pixel_counts are lists of float/int/None (same length as
        dates), or (None, None, None) for the three when want_dispersion is
        False. pixel_counts is the 'non_null_cells' t.rast.univar reported
        for each timestep, the sample size the dispersion statistic at that
        timestep was computed from.
    """
    kwargs = {"input": strds, "zones": zone_raster, "nprocs": nprocs}
    if where:
        kwargs["where"] = where
    flags = ""
    if statistic == "median":
        flags = "e"
        kwargs["percentile"] = 50
        value_name = "median"
    elif statistic == "percentile":
        flags = "e"
        kwargs["percentile"] = percentile_value
        value_name = percentile_column_name(percentile_value)
    elif statistic in ("min", "max"):
        value_name = statistic
    else:
        value_name = "mean"

    try:
        raw = gs.read_command("t.rast.univar", flags=flags, **kwargs)
    except CalledModuleError:
        gs.fatal(
            _(
                "t.rast.univar failed while sampling strds '{}' over the "
                "zone. Check that the dataset exists and that the zone "
                "overlaps the current computational region."
            ).format(strds)
        )

    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        gs.fatal(_("t.rast.univar returned no data for the given zone."))

    header = lines[0].split("|")
    start_idx = find_column(header, "start")
    value_idx = find_column(header, value_name)
    if start_idx is None or value_idx is None:
        gs.fatal(
            _(
                "Could not find the expected 'start'/'{}' columns in "
                "t.rast.univar output."
            ).format(value_name)
        )

    lower_idx = upper_idx = count_idx = None
    if want_dispersion:
        if statistic == "mean":
            lower_idx = find_column(header, "stddev")
            upper_idx = lower_idx
        else:
            lower_idx = find_column(header, "first_quartile")
            upper_idx = find_column(header, "third_quartile")
        if lower_idx is None or upper_idx is None:
            gs.fatal(
                _(
                    "Could not find the columns needed for the dispersion "
                    "band in t.rast.univar output."
                )
            )
        count_idx = find_column(header, "non_null_cells")

    dates = []
    values = []
    lowers = [] if want_dispersion else None
    uppers = [] if want_dispersion else None
    counts = [] if want_dispersion else None
    width = (
        max(start_idx, value_idx, lower_idx or 0, upper_idx or 0, count_idx or 0) + 1
    )
    for ln in lines[1:]:
        cols = ln.split("|")
        if len(cols) < width:
            continue
        dates.append(cols[start_idx])
        value = parse_zonal_token(cols[value_idx])
        values.append(value)
        if want_dispersion:
            if statistic == "mean":
                spread = parse_zonal_token(cols[lower_idx])
                lowers.append(
                    value - spread if value is not None and spread is not None else None
                )
                uppers.append(
                    value + spread if value is not None and spread is not None else None
                )
            else:
                lowers.append(parse_zonal_token(cols[lower_idx]))
                uppers.append(parse_zonal_token(cols[upper_idx]))
            count = (
                parse_zonal_token(cols[count_idx]) if count_idx is not None else None
            )
            counts.append(int(count) if count is not None else None)

    if not dates:
        gs.fatal(_("Could not parse any timesteps from t.rast.univar output."))
    return (dates, values, lowers, uppers, counts)


def sample_strds(
    strds,
    zone_raster,
    east,
    north,
    where,
    statistic,
    nprocs,
    want_dispersion=False,
    percentile_value=None,
):
    """Extract the series of a point or of a pooled zone from an strds.

    Dispatches to extract_zonal_series() when a zones raster is given (see
    sampling_location()), otherwise to extract_series() for the point.

    :param str strds: name of the input space-time raster dataset
    :param str|None zone_raster: single-category zones raster, or None for
        the point (east, north)
    :param float east: easting of the point (ignored for a zone)
    :param float north: northing of the point (ignored for a zone)
    :param str where: optional t.* WHERE clause to subset maps
    :param str statistic: zonal statistic, see extract_zonal_series()
    :param int nprocs: number of parallel processes
    :param bool want_dispersion: also return the dispersion band (zones
        only), see extract_zonal_series()
    :param float|None percentile_value: see extract_zonal_series()
    :return tuple: (dates, values, lowers, uppers, pixel_counts); the last
        three are None for a point or when want_dispersion is False
    """
    if zone_raster:
        return extract_zonal_series(
            strds=strds,
            zone_raster=zone_raster,
            where=where,
            statistic=statistic,
            nprocs=nprocs,
            want_dispersion=want_dispersion,
            percentile_value=percentile_value,
        )
    dates, values = extract_series(
        strds=strds, east=east, north=north, where=where, nprocs=nprocs
    )
    return dates, values, None, None, None


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


def parse_temporal_outliers(value, key):
    """Parse a 'temporal_outliers'/'temporal_outliers2' option into
    (threshold, window).

    :param str value: the option value, e.g. '0.3,15'; may be empty.
    :param str key: option name, used in error messages.
    :return tuple|None: (threshold, window), both positive floats, for
        detect_temporal_outliers(); or None if value is empty (the filter
        is disabled).
    """
    if not value:
        return None
    parts = value.split(",")
    if len(parts) != 2:
        gs.fatal(_("The '{}' option must be 'threshold,window'.").format(key))
    try:
        threshold, window = (float(p.strip()) for p in parts)
    except ValueError:
        gs.fatal(
            _("Could not parse '{}' value '{}' as two numbers.").format(key, value)
        )
    if threshold <= 0 or window <= 0:
        gs.fatal(_("Both values of '{}' must be positive numbers.").format(key))
    return threshold, window


def _find_excursions(values, offsets, threshold, window):
    """Find confirmed descend-then-rise excursions via a running peak/trough.

    The GRASS addon t.rast.event detects disturbance/recovery events in a
    strds the same way (tracking a running peak and following the signal
    down until it turns back up); this is that same running-peak idea,
    scoped down from t.rast.event's full event-recovery analysis to the
    yes/no "is this an isolated excursion" question this filter needs.

    A running peak tracks the highest value seen since the last confirmed
    excursion (or the series start). Once the series turns below it, every
    following point is tentatively "in descent": the running trough extends
    as the decline continues, however many observations that takes. The
    descent is confirmed -- and its interior points (between the peak and
    the point that comes back near it) are returned as the excursion -- once
    some later point returns to within half of ``threshold`` of the peak
    *and* the peak-to-trough drop reached ``threshold``. Unlike comparing
    each point to a fixed-size window (of several observations, or of just
    the nearest one), the peak stays pinned at the pre-excursion level for
    as long as the descent continues, so neither the excursion's own
    interior points nor the ordinary point where it ends up get judged
    against a baseline contaminated by the excursion itself.

    A descent still unconfirmed after ``window`` (measured from the peak) is
    abandoned without flagging anything, on the assumption it may be a
    genuine, sustained change rather than a transient artefact; the running
    peak then restarts from that point. This also means the series' final
    open descent, if any, is never flagged, since it never got the chance to
    confirm.

    :param numpy.ndarray values: observation values, in time order
    :param numpy.ndarray offsets: matching time offsets (days or steps)
    :param float threshold: minimum peak-to-trough drop to confirm
    :param float window: maximum time from the peak for the descent to
        confirm before it is abandoned as not transient
    :return numpy.ndarray: boolean mask (same length as ``values``) of
        confirmed excursion-interior points
    """
    n = len(values)
    excluded = np.zeros(n, dtype=bool)

    in_descent = False
    peak_val = values[0]
    peak_idx = 0
    trough_val = None
    descent_indices = []

    for i in range(1, n):
        if not in_descent:
            if values[i] >= peak_val:
                # Refresh peak_idx even on a tie, so a long flat run before a
                # descent doesn't leave window measured from a stale, much
                # earlier peak than the level actually just held.
                peak_val, peak_idx = values[i], i
            else:
                in_descent = True
                trough_val = values[i]
                descent_indices = [i]
            continue

        if offsets[i] - offsets[peak_idx] > window:
            # Taking too long to confirm: not an isolated excursion.
            in_descent = False
            peak_val, peak_idx = values[i], i
            descent_indices = []
            continue

        trough_val = min(trough_val, values[i])
        if values[i] >= peak_val - 0.5 * threshold:
            # Back near the peak: confirm the excursion if it was deep
            # enough, then restart peak tracking fresh from here.
            if peak_val - trough_val >= threshold:
                excluded[descent_indices] = True
            in_descent = False
            peak_val, peak_idx = values[i], i
            descent_indices = []
        else:
            descent_indices.append(i)

    return excluded


def detect_temporal_outliers(series, threshold, window, temporal_type="absolute"):
    """Flag isolated spikes/dips that revert within a short time window.

    A quality-control filter for transient artefacts (sensor noise, cloud
    contamination, a single bad pixel), not a general outlier remover: see
    ``_find_excursions()`` for how an excursion is confirmed. Dips and
    spikes are both covered by running that same peak/trough logic twice,
    once on the series and once negated (so a "descent" in the negated
    series is a rise in the real one); a deviation that is never confirmed
    to revert within ``window`` -- including a genuine, sustained change --
    is left untouched in both directions.

    :param pandas.Series series: irregular point series, before regularize()
    :param float threshold: minimum peak-to-trough deviation to flag an
        excursion, in the data's own units
    :param float window: maximum time, from the start of an excursion, for
        it to confirm before being treated as not transient, in calendar
        days (absolute time) or index steps (relative time)
    :param str temporal_type: 'absolute' or 'relative'
    :return tuple: (cleaned_series, excluded_series); excluded_series holds
        just the confirmed outliers (empty if none were found)
    """
    valid = series.dropna()
    if len(valid) < 3:
        return series, series.iloc[0:0]

    if temporal_type == "relative":
        offsets = valid.index.to_numpy(dtype="float64")
    else:
        # .total_seconds() (not '/ pd.Timedelta(days=1)') avoids a NumPy
        # timedelta64 'generic' unit deprecation warning on some pandas/NumPy
        # combinations.
        offsets = (valid.index - valid.index[0]).total_seconds().to_numpy() / 86400.0
    values = valid.to_numpy(dtype="float64")

    dips = _find_excursions(values, offsets, threshold, window)
    spikes = _find_excursions(-values, offsets, threshold, window)
    excluded_mask = dips | spikes

    excluded = valid[excluded_mask]
    return series.mask(series.index.isin(excluded.index)), excluded


def remove_temporal_outliers(series, threshold, window, temporal_type, name):
    """Apply the temporal_outliers= filter and fill the removed values.

    Runs detect_temporal_outliers() and, when it flags anything, reports it
    and fills just those dates by linear interpolation in time (by date for
    absolute time, by time step for relative time, so the observations need
    not be evenly spaced), ahead of the interpolation= method that later
    fills genuine gaps in regularize().
    An excursion can span many steps (up to 'window'), and a
    curvature-fitting method (quadratic, cubic, spline...) bridging a gap
    that wide can overshoot past either neighbour, replacing the outlier by
    a different, possibly larger artefact. Linear is bounded by its two
    neighbours and cannot do that. Genuine gaps (still NaN) are left alone.

    :param pandas.Series series: irregular series, before regularize()
    :param float threshold: see detect_temporal_outliers()
    :param float window: see detect_temporal_outliers()
    :param str temporal_type: 'absolute' or 'relative'
    :param str name: dataset name, for the message
    :return tuple: (filled_series, excluded_series); excluded_series holds
        the original values of the removed points (empty if none)
    """
    series, excluded = detect_temporal_outliers(
        series, threshold, window, temporal_type=temporal_type
    )
    if len(excluded):
        gs.message(
            _(
                "Flagged {n} value(s) in '{d}' as transient temporal "
                "outliers (threshold={t}, window={w}); interpolated "
                "linearly in time."
            ).format(n=len(excluded), d=name, t=threshold, w=window)
        )
        method = "index" if temporal_type == "relative" else "time"
        linear_filled = series.interpolate(method=method, limit_area="inside")
        series.loc[excluded.index] = linear_filled.loc[excluded.index]
    return series, excluded


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


def validate_frequency(frequency):
    """Check that the frequency= option, when given, is a pandas offset alias.

    The alias needs a unit, optionally with a multiplier, e.g. 'D', 'W',
    'MS', '16D', '5YS'. A bare number has no unit and pandas rejects it with
    an opaque message; this gives a clear one instead.

    :param str frequency: the frequency= option value (may be empty)
    """
    if not frequency:
        return
    try:
        pd.tseries.frequencies.to_offset(frequency)
    except (ValueError, TypeError):
        gs.fatal(
            _(
                "The 'frequency' value '{v}' is not a valid pandas offset "
                "alias. It needs a time unit, optionally with a leading "
                "multiplier, e.g. 'D' (day), 'W' (week), 'MS' (month "
                "start), '16D' (16 days), 'YS' or '5YS' (year start). A "
                "bare number is not accepted."
            ).format(v=frequency)
        )


def gap_runs(missing):
    """Find the runs of consecutive missing steps.

    :param numpy.ndarray missing: boolean array, True where a step is missing
    :return tuple: (starts, lengths), integer arrays with the position of the
        first step and the number of steps of each run
    """
    padded = np.concatenate(([False], missing, [False]))
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    starts, stops = edges[::2], edges[1::2]
    return starts, stops - starts


def longest_gap(interpolated):
    """Length of the longest run of interpolated steps.

    :param pandas.Series interpolated: boolean mask from regularize()
    :return int: number of steps, 0 if nothing was interpolated
    """
    _starts, lengths = gap_runs(interpolated.to_numpy())
    return int(lengths.max()) if len(lengths) else 0


def _step_name(value):
    """A regular-grid index value as text: a date, a date-time or a step."""
    if isinstance(value, pd.Timestamp):
        if value == value.normalize():
            return value.strftime("%Y-%m-%d")
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def regularize(
    series,
    frequency,
    method,
    order,
    temporal_type="absolute",
    step=None,
    tinfo=None,
    report=True,
    max_gap=None,
    name=None,
):
    """Resample onto a regular axis and interpolate gaps.

    STL requires an evenly spaced, gap-free series. To ensure this, data is resampled
    to the target frequency and the gaps between observations are interpolated.
    Steps before the first and after the last observation are left out rather
    than extrapolated, so the series spans the observed period only.

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
    :param bool report: print the inferred frequency (when 'frequency' is
        unset), the left-out leading and trailing steps, and the share of
        interpolated steps. False for the dispersion-band's extra regularize()
        calls, so the same things aren't reported three times over for one
        dataset.
    :param int|None max_gap: the longest run of missing steps that may be
        interpolated; a longer gap is a fatal error. None for no limit.
    :param str|None name: dataset name, for the messages

    :return tuple: (filled, interpolated); filled is the regular, gap-free
        pandas.Series, interpolated a boolean pandas.Series on the same
        index, True at the steps that had no observation
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
        if report:
            gs.message(
                _("Inferred a regular frequency of '{}' from the data.").format(
                    inferred
                )
            )
        resampled = series.asfreq(inferred)

    observed = np.flatnonzero(resampled.notna().to_numpy())
    if not len(observed):
        gs.fatal(_("'{}' has no observations to regularize.").format(name))
    n_leading = int(observed[0])
    n_trailing = len(resampled) - 1 - int(observed[-1])
    resampled = resampled.iloc[observed[0] : observed[-1] + 1]
    interpolated = resampled.isna()

    starts, lengths = gap_runs(interpolated.to_numpy())
    if max_gap is not None and len(lengths) and lengths.max() > max_gap:
        longest = int(np.argmax(lengths))
        first = starts[longest]
        last = first + lengths[longest] - 1
        gs.fatal(
            _(
                "'{d}' has {k} consecutive missing steps ({s} to {e}), more "
                "than max_gap={m}. Raise 'max_gap', or select a period "
                "without such a gap with 'where'."
            ).format(
                d=name,
                k=lengths[longest],
                s=_step_name(resampled.index[first]),
                e=_step_name(resampled.index[last]),
                m=max_gap,
            )
        )
    if report:
        if n_leading or n_trailing:
            gs.message(
                _(
                    "Left out {a} leading and {b} trailing step(s) without "
                    "data in '{d}'; the series runs from {s} to {e}."
                ).format(
                    a=n_leading,
                    b=n_trailing,
                    d=name,
                    s=_step_name(resampled.index[0]),
                    e=_step_name(resampled.index[-1]),
                )
            )
        n_missing = int(interpolated.sum())
        if n_missing:
            gs.message(
                _(
                    "Interpolated {k} of {n} steps ({p:.0%}) in '{d}'; the "
                    "longest gap is {g} step(s)."
                ).format(
                    k=n_missing,
                    n=len(resampled),
                    p=n_missing / len(resampled),
                    d=name,
                    g=int(lengths.max()),
                )
            )

    interp_kwargs = {"method": method, "limit_area": "inside"}
    if method in ("spline", "polynomial"):
        if not order:
            gs.fatal(
                _("The '{}' interpolation method requires the 'order' option.").format(
                    method
                )
            )
        interp_kwargs["order"] = int(order)

    filled = resampled.interpolate(**interp_kwargs)

    if filled.isna().any():
        gs.fatal(_("Series still contains gaps after interpolation; cannot run STL."))
    if len(filled) < 4:
        gs.fatal(
            _("Too few observations ({}) after regularization to run STL.").format(
                len(filled)
            )
        )
    return filled, interpolated
