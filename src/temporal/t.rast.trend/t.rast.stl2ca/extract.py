############################################################################
#
# MODULE:       t.rast.stl2ca (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Data-extraction and regularization helpers for t.rast.stl2ca:
#               building the per-category zones raster (from a CELL raster's
#               own cell values, or from a vector attribute column), parsing
#               the t.rast.univar output into one series per category, and
#               resampling each series onto a regular, gap-free axis.
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

"""Data extraction, category-raster preparation and regularization for
t.rast.stl2ca.

np/pd are set by t.rast.stl2ca.lazy_import_py_modules() -- after GRASS parses
the command line -- rather than imported here, so a plain module scan
(--help, g.extension) never needs numpy/pandas installed.
"""

import os

import grass.script as gs
from grass.exceptions import CalledModuleError

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by t.rast.stl2ca.lazy_import_py_modules() before any function below runs.
np = None
pd = None

# Temporary dirs/rasters created during extraction, removed by
# t.rast.stl2ca.cleanup() at exit (imported there via 'from extract import').
# The user's own raster= input is never added here (see validate_category_raster()).
clean_dirs = []
clean_rasters = []


def find_column(header, name):
    """Return the index of a column named ``name`` in a pipe-table header.

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


def validate_category_raster(raster):
    """Check that raster= exists, is CELL type and has at least one category.

    :param str raster: name of the raster map (as given on the command line)
    :return str: the map's full name (mapset-qualified)
    """
    found = gs.find_file(name=raster, element="cell")
    fullname = found.get("fullname")
    if not fullname:
        gs.fatal(_("Raster map '{}' not found.").format(raster))
    info = gs.raster_info(raster)
    if info.get("datatype") != "CELL":
        gs.fatal(
            _(
                "Raster map '{}' is {} but 'raster' must be CELL (integer) "
                "type, since its cell values are used directly as category "
                "codes."
            ).format(raster, info.get("datatype"))
        )
    return fullname


def validate_vector(vector):
    """Check that the vector map exists.

    :param str vector: name of the vector map (as given on the command line)
    :return str: the map's full name (mapset-qualified)
    """
    found = gs.find_file(name=vector, element="vector")
    fullname = found.get("fullname")
    if not fullname:
        gs.fatal(_("Vector map '{}' not found.").format(vector))
    return fullname


def shrink_region_to_raster(raster):
    """Shrink the (already temporary) computational region to raster's own
    non-null data extent, keeping the current resolution.

    g.region's zoom= already intersects with whatever region is current
    rather than expanding past it, so this is a direct, safe shrink: cells
    outside a category's own extent never contributed to its statistics
    anyway, so this only reduces how much t.rast.univar has to sweep later,
    never changes a result. Called on a region set up with
    grass.script.use_temp_region(), so the user's own region is untouched.

    :param str raster: name of the raster map (mapset-qualified)
    """
    gs.run_command("g.region", zoom=raster)


def shrink_region_to_vector(vector):
    """Shrink the (already temporary) computational region to vector's own
    bounding box, intersected with whatever region is current, keeping the
    current resolution.

    Unlike g.region zoom= (see shrink_region_to_raster()), g.region's
    vector=/-a combination expands the region to the vector's full bounding
    box regardless of the current region, so the intersection is computed
    by hand here -- this must only ever shrink the region, never grow it
    past what the caller already had, or a category could end up sampled
    over an area the user never asked for. Called on a region set up with
    grass.script.use_temp_region(), so the user's own region is untouched.

    :param str vector: name of the vector map (mapset-qualified)
    """
    orig = gs.region()
    gs.run_command("g.region", vector=vector, flags="a")
    new = gs.region()
    n = min(orig["n"], new["n"])
    s = max(orig["s"], new["s"])
    e = min(orig["e"], new["e"])
    w = max(orig["w"], new["w"])
    if n <= s or e <= w:
        gs.fatal(
            _(
                "Vector map '{}' has no features within the current "
                "computational region; nothing to sample."
            ).format(vector)
        )
    gs.run_command("g.region", n=n, s=s, e=e, w=w, flags="a")


def vector_category_raster(vector, layer, column):
    """Build a categories raster from a vector map's attribute column.

    Every feature is first rasterized with its own 'cat' value (so a
    multi-feature vector gets one raster category per feature); when
    ``column`` is anything other than 'cat', features sharing the same
    ``column`` value are then collapsed onto one shared category, via
    r.reclass, with that value (as text) set as the category's label. This
    works the same way whether ``column`` holds numbers or text, and needs
    no attribute lookup at all when ``column`` is 'cat' (the default),
    since every feature is then already its own category.

    :param str vector: name of the input vector map (mapset-qualified)
    :param str layer: vector layer (field) number or name
    :param str column: attribute column defining the category grouping, or
        'cat' for one category per feature
    :return str: name of the created categories raster (registered in
        ``clean_rasters`` for removal by cleanup())
    """
    cat_raster = gs.tempname(12)
    try:
        gs.run_command(
            "v.to.rast",
            input=vector,
            layer=layer,
            output=cat_raster,
            use="cat",
            quiet=True,
        )
    except CalledModuleError:
        gs.fatal(
            _(
                "Could not rasterize vector map '{}' (layer {}). Check that "
                "the layer exists and has features within the current "
                "computational region."
            ).format(vector, layer)
        )
    clean_rasters.append(cat_raster)

    if column == "cat":
        return cat_raster

    try:
        table = gs.read_command(
            "v.db.select",
            map=vector,
            layer=layer,
            columns="cat,{}".format(column),
            separator="pipe",
            flags="c",
            quiet=True,
        )
    except CalledModuleError:
        gs.fatal(
            _(
                "Could not read column '{col}' (layer {lyr}) from vector map "
                "'{v}'. Check that the column exists and that layer {lyr} "
                "has an attribute table."
            ).format(col=column, lyr=layer, v=vector)
        )

    pairs = []
    for line in table.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        try:
            cat_value = int(parts[0])
        except ValueError:
            continue
        pairs.append((cat_value, parts[1]))
    if not pairs:
        gs.fatal(
            _("Column '{}' of vector map '{}' has no values to group by.").format(
                column, vector
            )
        )

    # Distinct group values, in a stable order: numeric ascending when every
    # value parses as a number, else alphabetical. Each gets its own new
    # integer category code (r.reclass output), labelled with the original
    # (text or numeric) value.
    seen = []
    seen_set = set()
    for _cat, value in pairs:
        if value not in seen_set:
            seen_set.add(value)
            seen.append(value)
    try:
        ordered = sorted(seen, key=float)
    except ValueError:
        ordered = sorted(seen)
    code_of = {value: code for code, value in enumerate(ordered, start=1)}

    tmpdir = gs.tempdir()
    clean_dirs.append(tmpdir)
    rules_file = os.path.join(tmpdir, "category_reclass.rules")
    with open(rules_file, "w") as fh:
        for cat_value, value in pairs:
            fh.write("{} = {} {}\n".format(cat_value, code_of[value], value))

    zone_raster = gs.tempname(12)
    try:
        gs.run_command(
            "r.reclass",
            input=cat_raster,
            output=zone_raster,
            rules=rules_file,
            quiet=True,
        )
    except CalledModuleError:
        gs.fatal(
            _("Could not group vector map '{}' by column '{}'.").format(vector, column)
        )
    clean_rasters.append(zone_raster)
    return zone_raster


def discover_categories(zone_raster):
    """List the distinct non-null categories actually present in a raster.

    Uses r.stats (-n excludes the null row, -l adds the category label) so
    the result reflects what is really in the raster within the current
    computational region, rather than a possibly stale/incomplete category
    table. A category without an explicit label (e.g. a plain raster=
    input, or a vector 'cat' grouping) falls back to its value as a string.

    :param str zone_raster: name of the categories raster (raster= input,
        or the raster built by vector_category_raster())
    :return list: sorted list of (int value, str label) tuples
    """
    try:
        raw = gs.read_command(
            "r.stats", flags="nl", input=zone_raster, separator="pipe", quiet=True
        )
    except CalledModuleError:
        gs.fatal(
            _("Could not list the categories present in '{}'.").format(zone_raster)
        )

    categories = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 1)
        try:
            value = int(parts[0])
        except (ValueError, IndexError):
            continue
        label = parts[1].strip() if len(parts) > 1 and parts[1].strip() else str(value)
        categories.append((value, label))
    if not categories:
        gs.fatal(
            _(
                "No categories found within the current computational "
                "region; nothing to sample."
            )
        )
    return sorted(categories)


def filter_categories(categories, categories_opt):
    """Restrict a discovered category list to the 'categories=' option.

    Each requested token is matched against either the category's integer
    value or its label (as strings); every token must match something.

    :param list categories: (value, label) tuples from discover_categories()
    :param str categories_opt: raw 'categories=' option value (may be empty)
    :return list: the matching subset of ``categories``, in its original order
    """
    if not categories_opt:
        return categories
    requested = [c.strip() for c in categories_opt.split(",") if c.strip()]
    by_token = {}
    for value, label in categories:
        by_token.setdefault(str(value), (value, label))
        by_token.setdefault(label, (value, label))

    selected = []
    seen_values = set()
    for token in requested:
        match = by_token.get(token)
        if match is None:
            gs.fatal(
                _(
                    "'{}' in 'categories' does not match any category found "
                    "(available: {})."
                ).format(token, ", ".join(label for _v, label in categories))
            )
        if match[0] not in seen_values:
            seen_values.add(match[0])
            selected.append(match)
    return selected


def extract_zonal_series_multi(
    strds, zone_raster, where, statistic, nprocs, want_dispersion, percentile_value=None
):
    """Extract one (date, value) series per category from an strds.

    A single t.rast.univar call (zones=zone_raster) covers every registered
    timestep and every category present in zone_raster at once: with a
    multi-category zones raster it reports one row per category per
    timestep (a 'zone' column identifies which), so this parses that into
    one series per category instead of t.rast.univar needing to be called
    once per category.

    'mean', 'min' and 'max' use the plain (non-extended) statistics, which
    already include the standard deviation and the min/max columns. 'median'
    and 'percentile' require t.rast.univar's extended-statistics mode (-e);
    for 'median' this also yields the first/third quartiles used for the
    dispersion band, at no extra cost. Extended statistics sort all cell
    values in memory per map, a real cost on very large rasters.

    :param str strds: name of the input space-time raster dataset
    :param str zone_raster: name of the (multi-category) zones raster
    :param str where: optional t.* WHERE clause to subset maps
    :param str statistic: 'mean', 'median', 'min', 'max' or 'percentile'
    :param int nprocs: number of parallel processes for t.rast.univar
    :param bool want_dispersion: also return the lower/upper dispersion band
        (mean +/- stddev, or the first/third quartile for median); only
        valid with statistic 'mean' or 'median'
    :param float|None percentile_value: percentile (0-100) to use when
        statistic is 'percentile'; ignored otherwise

    :return dict: {category_value: (dates, values, lowers, uppers, counts)},
        one entry per category found in the t.rast.univar output; the last
        three are lists of float/int/None (same length as dates), or
        (None, None, None) for all categories when want_dispersion is False.
        counts is the 'non_null_cells' t.rast.univar reported, the sample
        size the dispersion statistic at that timestep was computed from. A
        category present in zone_raster but never reported by t.rast.univar
        (no overlap with any registered map) is simply absent from the dict.
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
                "categories. Check that the dataset exists and that the "
                "categories overlap the current computational region."
            ).format(strds)
        )

    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        gs.fatal(_("t.rast.univar returned no data for the given categories."))

    header = lines[0].split("|")
    start_idx = find_column(header, "start")
    zone_idx = find_column(header, "zone")
    value_idx = find_column(header, value_name)
    if start_idx is None or zone_idx is None or value_idx is None:
        gs.fatal(
            _(
                "Could not find the expected 'start'/'zone'/'{}' columns in "
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

    width = (
        max(
            start_idx,
            zone_idx,
            value_idx,
            lower_idx or 0,
            upper_idx or 0,
            count_idx or 0,
        )
        + 1
    )
    by_category = {}
    for ln in lines[1:]:
        cols = ln.split("|")
        if len(cols) < width:
            continue
        try:
            zone_value = int(cols[zone_idx])
        except ValueError:
            continue
        series = by_category.setdefault(
            zone_value,
            {"dates": [], "values": [], "lowers": [], "uppers": [], "counts": []},
        )
        series["dates"].append(cols[start_idx])
        value = parse_zonal_token(cols[value_idx])
        series["values"].append(value)
        if want_dispersion:
            if statistic == "mean":
                spread = parse_zonal_token(cols[lower_idx])
                series["lowers"].append(
                    value - spread if value is not None and spread is not None else None
                )
                series["uppers"].append(
                    value + spread if value is not None and spread is not None else None
                )
            else:
                series["lowers"].append(parse_zonal_token(cols[lower_idx]))
                series["uppers"].append(parse_zonal_token(cols[upper_idx]))
            count = (
                parse_zonal_token(cols[count_idx]) if count_idx is not None else None
            )
            series["counts"].append(int(count) if count is not None else None)

    if not by_category:
        gs.fatal(_("Could not parse any timesteps from t.rast.univar output."))

    result = {}
    for zone_value, series in by_category.items():
        lowers = series["lowers"] if want_dispersion else None
        uppers = series["uppers"] if want_dispersion else None
        counts = series["counts"] if want_dispersion else None
        result[zone_value] = (series["dates"], series["values"], lowers, uppers, counts)
    return result


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
    series,
    frequency,
    method,
    order,
    temporal_type="absolute",
    step=None,
    tinfo=None,
    report=True,
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
    :param bool report: print the inferred-frequency message when 'frequency'
        is unset. False for the dispersion-band's extra regularize() calls,
        so the same inference isn't reported three times over for one dataset.

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
        if report:
            gs.message(
                _("Inferred a regular frequency of '{}' from the data.").format(
                    inferred
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
