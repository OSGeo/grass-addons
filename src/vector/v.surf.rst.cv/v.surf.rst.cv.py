#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.surf.rst.cv
# AUTHOR(S):    Corey T. White, NCSU GeoForAll Lab
# PURPOSE:      Cross-validation procedure for optimizing regularized spline
#               with tension (RST) interpolation parameters for v.surf.rst.
# COPYRIGHT:    (C) 2025 OpenPlains Inc. and the GRASS Development Team
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Performs a cross-validation procedure to optimize the parameterization of v.surf.rst.
# % keyword: vector
# % keyword: surface
# % keyword: interpolation
# % keyword: cross-validation
# % keyword: RST
# % keyword: splines
# % keyword: parallel
# %end

# %option G_OPT_V_INPUT
# % key: point_cloud
# % label: Name of the input point vector map
# % guisection: Input
# %end

# %option G_OPT_R_INPUT
# % key: mask
# % label: Name of the raster map used as mask
# % required: no
# % guisection: Input
# %end

# %option
# % key: tension
# % type: double
# % required: no
# % multiple: yes
# % answer: 10,20,40,80,160
# % label: Tension parameter values to cross-validate
# % guisection: Cross-Validation
# %end

# %option
# % key: smooth
# % type: double
# % required: no
# % multiple: yes
# % answer: 0.001,0.01,0.1,1.0,10.0
# % label: Smoothing parameter values to cross-validate
# % guisection: Cross-Validation
# %end

# %option
# % key: npmin
# % type: integer
# % required: no
# % multiple: yes
# % label: Minimum number of points for approximation in a segment (>segmax)
# % description: Multiple values are swept as an outer loop
# % guisection: Cross-Validation
# %end

# %option
# % key: segmax
# % type: integer
# % required: no
# % multiple: yes
# % label: Maximum number of points in a segment
# % description: Multiple values are swept as an outer loop
# % guisection: Cross-Validation
# %end

# %option
# % key: dmin
# % type: double
# % required: no
# % multiple: yes
# % label: Minimum distance between points (to remove almost identical points)
# % description: Multiple values are swept as an outer loop
# % guisection: Cross-Validation
# %end

# %option
# % key: dmax
# % type: double
# % required: no
# % multiple: yes
# % label: Maximum distance between points on isoline (to insert additional points)
# % description: Multiple values are swept as an outer loop
# % guisection: Cross-Validation
# %end

# %option
# % key: theta
# % type: double
# % required: no
# % multiple: yes
# % label: Anisotropy angle (in degrees counterclockwise from East)
# % description: Multiple values are swept as an outer loop
# % guisection: Cross-Validation
# %end

# %option
# % key: scalex
# % type: double
# % required: no
# % multiple: yes
# % label: Anisotropy scaling factor
# % description: Multiple values are swept as an outer loop
# % guisection: Cross-Validation
# %end

# %option
# % key: method
# % type: string
# % required: no
# % options: grid,refine
# % answer: grid
# % description: Search method over tension and smoothing (grid: full Cartesian product; refine: recursive refinement around the best cell)
# % guisection: Cross-Validation
# %end

# %option
# % key: levels
# % type: integer
# % required: no
# % answer: 3
# % description: Maximum number of refinement levels for method=refine
# % guisection: Cross-Validation
# %end

# %option
# % key: npoints
# % type: integer
# % required: no
# % description: Cross-validate on a spatially stratified subsample of approximately this many points
# % guisection: Cross-Validation
# %end

# %option G_OPT_M_SEED
# % guisection: Cross-Validation
# %end

# %option G_OPT_V_FIELD
# % guisection: RST Parameters
# % required: no
# %end

# %option G_OPT_DB_COLUMN
# % key: zcolumn
# % label: Name of the attribute column with values to be used for approximation
# % description: If not given and input is 2D vector map then category values are used. If input is 3D vector map then z-coordinates are used.
# % required: no
# % guisection: RST Parameters
# %end

# %option G_OPT_DB_WHERE
# % key: where
# % label: WHERE conditions of SQL statement without 'where' keyword
# % description: Example: elevation < 500 and elevation >= 1
# % required: no
# % guisection: RST Parameters
# %end

# %option
# % key: zscale
# % type: double
# % required: no
# % answer: 1.0
# % description: Conversion factor for values used for approximation
# % guisection: RST Parameters
# %end

# %option
# % key: cv_prefix
# % label: Prefix to use for cross-validation output maps
# % type: string
# % required: no
# % description: Prefix for saved cross-validation error vector maps and interpolated deviation surfaces. If not set, cross-validation maps are temporary.
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key: output_file
# % label: Output file
# % description: Output file for the results in the selected format
# % required: no
# % guisection: Output
# %end

# %option G_OPT_F_FORMAT
# % options: plain,csv,json
# % answer: plain
# % descriptions: plain;Human readable table;csv;CSV (Comma Separated Values);json;JSON (JavaScript Object Notation)
# % guisection: Output
# %end

# %option G_OPT_M_NPROCS
# %end

# %flag
# % key: t
# % description: Use scale dependent tension (recommended when tuning, makes tension transferable across point densities)
# %end

from __future__ import annotations

import atexit
import csv
import io
import itertools
import json
import math
import os
import queue
import random
import shutil
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import grass.script as gs
from grass.exceptions import CalledModuleError

# Parameters swept as an outer loop around the tension x smooth search.
# npmin and segmax change the solver setup; dmin and dmax change the
# cross-validation sample itself; theta and scalex change the model.
STRUCTURAL_PARAMS = ("npmin", "segmax", "dmin", "dmax", "theta", "scalex")
INT_PARAMS = {"npmin", "segmax"}

# v.surf.rst compiled-in defaults (vector/v.surf.rst/surf.h) used for
# reporting when the user does not override them.
VSURFRST_DEFAULT_NPMIN = 300

# Relative RMSE spread across a refinement window below which refinement stops.
REFINE_SPREAD_TOLERANCE = 0.005

RUN_COUNT_WARNING = 100

METRIC_KEYS = ("rmse", "mae", "nmad")

TMP_MAPS = []
TMP_MAPSET_PATHS = []


def cleanup():
    """Remove temporary vector maps and worker mapsets"""
    if TMP_MAPS:
        gs.run_command(
            "g.remove",
            type="vector",
            name=TMP_MAPS,
            flags="f",
            quiet=True,
            errors="ignore",
        )
    for path in TMP_MAPSET_PATHS:
        shutil.rmtree(path, ignore_errors=True)


class WorkerMapsets:
    """Pool of temporary mapsets so parallel v.surf.rst runs write into
    separate attribute databases instead of contending for the mapset's
    single SQLite database.

    Hand-rolled instead of grass.experimental.TemporaryMapsetSession
    because the grass.experimental API is explicitly unstable."""

    def __init__(self, count: int):
        self.queue = queue.Queue()
        genv = gs.gisenv()
        location_path = Path(genv["GISDBASE"]) / genv["LOCATION_NAME"]
        region = gs.region()
        search_path = gs.read_command(
            "g.mapsets", flags="p", separator="comma", quiet=True
        ).strip()
        for _ in range(count):
            name = f"tmp_cv_{str(uuid.uuid4()).replace('-', '_')}"
            mapset_path = location_path / name
            mapset_path.mkdir()
            TMP_MAPSET_PATHS.append(mapset_path)
            shutil.copy(location_path / genv["MAPSET"] / "WIND", mapset_path / "WIND")
            gisrc = Path(gs.tempfile())
            gisrc.write_text(
                f"GISDBASE: {genv['GISDBASE']}\n"
                f"LOCATION_NAME: {genv['LOCATION_NAME']}\n"
                f"MAPSET: {name}\n"
            )
            env = os.environ.copy()
            env["GISRC"] = str(gisrc)
            # Materialize the caller's effective region in the new mapset
            env.pop("WIND_OVERRIDE", None)
            env.pop("GRASS_REGION", None)
            gs.run_command(
                "g.region",
                env=env,
                quiet=True,
                **{key: region[key] for key in ("n", "s", "e", "w", "nsres", "ewres")},
            )
            gs.run_command(
                "g.mapsets",
                operation="set",
                mapset=f"{name},{search_path}",
                env=env,
                quiet=True,
            )
            self.queue.put((env, name))


def tmp_map_name(base: str) -> str:
    """Generate and register a temporary map name"""
    name = f"tmp_{base}_{str(uuid.uuid4()).replace('-', '_')}"
    TMP_MAPS.append(name)
    return name


def parse_number_list(value: str, key: str) -> list[float | int]:
    """Parse a comma separated option value into numbers"""
    if not value:
        return []
    result = []
    for item in value.split(","):
        item = item.strip()
        try:
            result.append(int(item) if key in INT_PARAMS else float(item))
        except ValueError:
            gs.fatal(
                _("Invalid value '{value}' for option {key}").format(
                    value=item, key=key
                )
            )
    return result


def percentile(sorted_values: list[float], q: float) -> float:
    """Linearly interpolated percentile of pre-sorted values (q in 0-100)"""
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    pos = (q / 100.0) * (n - 1)
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return sorted_values[lower]
    frac = pos - lower
    return sorted_values[lower] * (1 - frac) + sorted_values[upper] * frac


def residual_metrics(residuals: list[float]) -> dict:
    """Summary statistics of cross-validation residuals (predicted - observed)"""
    n = len(residuals)
    mean = sum(residuals) / n
    rmse = math.sqrt(sum(r * r for r in residuals) / n)
    mae = sum(abs(r) for r in residuals) / n
    ordered = sorted(residuals)
    median = percentile(ordered, 50)
    nmad = 1.4826 * percentile(sorted(abs(r - median) for r in residuals), 50)
    abs_ordered = sorted(abs(r) for r in residuals)
    return {
        "n": n,
        "me": mean,
        "mae": mae,
        "rmse": rmse,
        "median": median,
        "nmad": nmad,
        "p68": percentile(abs_ordered, 68.3),
        "p95": percentile(abs_ordered, 95.0),
        "min": ordered[0],
        "max": ordered[-1],
    }


def extract_residuals(
    cvdev_map: str, zscale: float, env: dict | None = None
) -> list[float]:
    """Read cross-validation residuals (flt1 column) from a cvdev vector map"""
    data = gs.parse_command(
        "v.db.select", map=cvdev_map, format="json", quiet=True, env=env
    )
    return [float(rec["flt1"]) / zscale for rec in data["records"]]


class CrossValidator:
    """Runs v.surf.rst leave-one-out cross-validation for parameter combinations"""

    def __init__(
        self,
        *,
        points: str,
        base_args: dict,
        scale_dependent: bool,
        zscale: float,
        cv_prefix: str | None,
        workers: int,
        dnorm_area: float,
    ):
        self.points = points
        self.base_args = base_args
        self.flags = "ct" if scale_dependent else "c"
        self.scale_dependent = scale_dependent
        self.zscale = zscale
        self.cv_prefix = cv_prefix
        self.workers = workers
        self.dnorm_area = dnorm_area
        self.counter = itertools.count(1)
        self.results = []
        self.mapsets = None
        if workers > 1:
            try:
                self.mapsets = WorkerMapsets(workers)
            except OSError as error:
                gs.warning(
                    _(
                        "Cannot create temporary mapsets ({error}); running "
                        "cross-validations sequentially."
                    ).format(error=error)
                )
                self.workers = 1

    def run_one(self, task: tuple[int, dict]) -> dict:
        """Run one leave-one-out cross-validation and compute its metrics"""
        index, params = task
        if self.cv_prefix:
            cvdev = f"{self.cv_prefix}_{index:03d}"
        else:
            cvdev = tmp_map_name("cvdev")
        row = dict(params)
        row["cvdev"] = cvdev if self.cv_prefix else None
        args = {k: v for k, v in params.items() if v is not None}
        env, worker_mapset = self.mapsets.queue.get() if self.mapsets else (None, None)
        try:
            gs.run_command(
                "v.surf.rst",
                input=self.points,
                cvdev=cvdev,
                nprocs=1,
                flags=self.flags,
                quiet=True,
                overwrite=True,
                env=env,
                **self.base_args,
                **args,
            )
            residuals = extract_residuals(cvdev, self.zscale, env=env)
            if not residuals:
                raise ValueError(_("cross-validation produced no residuals"))
            row.update(residual_metrics(residuals))
            row["error"] = None
            if self.cv_prefix and worker_mapset:
                gs.run_command(
                    "g.copy",
                    vector=f"{cvdev}@{worker_mapset},{cvdev}",
                    quiet=True,
                    overwrite=True,
                )
        except (CalledModuleError, ValueError, KeyError) as error:
            gs.warning(
                _("Cross-validation failed for {params}: {error}").format(
                    params=args, error=error
                )
            )
            row["error"] = " ".join(str(error).split())
        finally:
            if self.mapsets:
                self.mapsets.queue.put((env, worker_mapset))
        if row["error"] is None:
            row["dnorm"] = self.computed_dnorm(row)
            if self.scale_dependent:
                row["tension_rescaled"] = row["tension"] * row["dnorm"] / 1000.0
        if not self.cv_prefix and not worker_mapset:
            gs.run_command(
                "g.remove",
                type="vector",
                name=cvdev,
                flags="f",
                quiet=True,
                errors="ignore",
            )
        if cvdev in TMP_MAPS:
            TMP_MAPS.remove(cvdev)
        return row

    def computed_dnorm(self, row: dict) -> float:
        """Approximate the dnorm v.surf.rst computes internally.

        dnorm = sqrt(area * npmin / n) over the accepted points
        (vector/v.surf.rst/main.c). The residual count stands in for the
        internal point count, so this is approximate when the region clips
        points.
        """
        npmin = row.get("npmin") or VSURFRST_DEFAULT_NPMIN
        return math.sqrt(self.dnorm_area * npmin / row["n"])

    def run_batch(self, param_list: list[dict]) -> list[dict]:
        """Run a batch of parameter combinations in parallel.

        Output map indices are assigned before submission so the mapping of
        cv_prefix map names to parameter combinations does not depend on
        thread scheduling.
        """
        tasks = [(next(self.counter), params) for params in param_list]
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            rows = list(pool.map(self.run_one, tasks))
        self.results.extend(rows)
        return rows


def geometric_midpoint(a: float, b: float) -> float:
    return math.sqrt(a * b)


def refine_axis(values: list[float], best: float) -> list[float]:
    """Log-scale bracket around the best value with geometric midpoints"""
    ordered = sorted(values)
    i = ordered.index(best)
    lo = ordered[max(0, i - 1)]
    hi = ordered[min(len(ordered) - 1, i + 1)]
    axis = {lo, hi, best}
    if lo < best:
        axis.add(geometric_midpoint(lo, best))
    if best < hi:
        axis.add(geometric_midpoint(best, hi))
    return sorted(axis)


def refine_search(
    validator: CrossValidator,
    tension_list: list[float],
    smooth_list: list[float],
    structural: dict,
    levels: int,
) -> None:
    """Recursive log-scale refinement of tension x smooth around the best cell"""
    evaluated = {}

    def evaluate(pairs):
        todo = [p for p in pairs if p not in evaluated]
        rows = validator.run_batch(
            [dict(structural, tension=t, smooth=s) for t, s in todo]
        )
        for pair, row in zip(todo, rows):
            evaluated[pair] = row

    evaluate(list(itertools.product(tension_list, smooth_list)))

    for level in range(levels):
        ok = {p: r for p, r in evaluated.items() if r["error"] is None}
        if not ok:
            gs.warning(_("All cross-validation runs failed, stopping refinement."))
            return
        best_pair = min(ok, key=lambda p: ok[p]["rmse"])
        tensions = sorted({p[0] for p in evaluated})
        smooths = sorted({p[1] for p in evaluated})
        t_axis = refine_axis(tensions, best_pair[0])
        s_axis = refine_axis(smooths, best_pair[1])
        window = [p for p in itertools.product(t_axis, s_axis) if p in ok]
        window_rmse = [ok[p]["rmse"] for p in window]
        if len(window_rmse) > 1:
            spread = max(window_rmse) - min(window_rmse)
            if spread / max(min(window_rmse), 1e-12) < REFINE_SPREAD_TOLERANCE:
                gs.verbose(
                    _(
                        "Refinement stopped at level {level}: RMSE spread "
                        "below tolerance"
                    ).format(level=level)
                )
                break
        new_pairs = [p for p in itertools.product(t_axis, s_axis) if p not in evaluated]
        if not new_pairs:
            break
        gs.message(
            _("Refinement level {level}: evaluating {count} combinations").format(
                level=level + 1, count=len(new_pairs)
            )
        )
        evaluate(new_pairs)

    ok = {p: r for p, r in evaluated.items() if r["error"] is None}
    if ok:
        best_pair = min(ok, key=lambda p: ok[p]["rmse"])
        if best_pair[0] in (min(tension_list), max(tension_list)) or best_pair[1] in (
            min(smooth_list),
            max(smooth_list),
        ):
            gs.warning(
                _(
                    "Best tension/smoothing found on the boundary of the searched "
                    "range; widen the tension or smooth range and rerun."
                )
            )


def spatial_subsample(
    points: str, layer: str, npoints: int, seed: int | None, bbox: dict
) -> str:
    """Extract a spatially stratified random subsample of approximately npoints.

    One point is drawn per cell of a coarse grid sized so the grid holds about
    npoints cells; the selection is then topped up or thinned to npoints.
    """
    rng = random.Random(seed)
    dx = max(bbox["east"] - bbox["west"], 1e-12)
    dy = max(bbox["north"] - bbox["south"], 1e-12)
    cell = math.sqrt(dx * dy / npoints)
    cells = {}
    # Bounded reservoir of extra categories to top the selection up to
    # npoints when fewer than npoints grid cells are occupied
    extras = []
    total = 0
    process = gs.pipe_command(
        "v.out.ascii",
        input=points,
        layer=layer,
        type="point",
        format="point",
        separator=",",
        quiet=True,
    )
    for line in process.stdout:
        fields = gs.decode(line).strip().split(",")
        try:
            x, y = float(fields[0]), float(fields[1])
            cat = int(fields[-1])
        except (ValueError, IndexError):
            continue
        total += 1
        key = (int((x - bbox["west"]) / cell), int((y - bbox["south"]) / cell))
        # Reservoir sample of one category per grid cell
        count, kept = cells.get(key, (0, None))
        count += 1
        if rng.randrange(count) == 0:
            kept = cat
        cells[key] = (count, kept)
        if len(extras) < 2 * npoints:
            extras.append(cat)
        elif rng.randrange(total) < 2 * npoints:
            extras[rng.randrange(2 * npoints)] = cat
    if process.wait() != 0:
        gs.fatal(
            _("Unable to read coordinates from <{name}> for subsampling").format(
                name=points
            )
        )
    if not cells:
        gs.fatal(
            _(
                "Subsampling requires points with category values; <{name}> has none"
            ).format(name=points)
        )
    if total <= npoints:
        gs.warning(
            _(
                "Input has only {count} points with categories, subsampling skipped."
            ).format(count=total)
        )
        return points

    selected = [kept for _count, kept in cells.values()]
    if len(selected) > npoints:
        selected = rng.sample(selected, npoints)
    elif len(selected) < npoints:
        chosen = set(selected)
        top_up = [c for c in extras if c not in chosen]
        rng.shuffle(top_up)
        selected.extend(top_up[: npoints - len(selected)])

    subsample = tmp_map_name("subsample")
    cat_file = gs.tempfile()
    Path(cat_file).write_text(
        "\n".join(str(c) for c in sorted(selected)) + "\n", encoding="utf-8"
    )
    gs.run_command(
        "v.extract",
        input=points,
        layer=layer,
        output=subsample,
        file=cat_file,
        quiet=True,
    )
    gs.message(
        _(
            "Cross-validating on a spatial subsample of {count} of {total} points"
        ).format(count=len(selected), total=total)
    )
    return subsample


def best_rows(results: list[dict]) -> dict:
    """Best row per metric among successful runs"""
    ok = [r for r in results if r["error"] is None]
    if not ok:
        return {}
    return {metric: min(ok, key=lambda r: r[metric]) for metric in METRIC_KEYS}


def format_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def result_columns(results: list[dict], swept: list[str]) -> list[str]:
    columns = ["tension", "smooth"]
    columns.extend(p for p in STRUCTURAL_PARAMS if p in swept)
    if any(r.get("tension_rescaled") is not None for r in results):
        columns.append("tension_rescaled")
    columns.extend(
        [
            "n",
            "rmse",
            "mae",
            "nmad",
            "me",
            "median",
            "p68",
            "p95",
            "min",
            "max",
            "dnorm",
        ]
    )
    if any(r["cvdev"] for r in results):
        columns.append("cvdev")
    if any(r["error"] for r in results):
        columns.append("error")
    return columns


def plain_output(results: list[dict], swept: list[str]) -> str:
    columns = result_columns(results, swept)
    table = [columns]
    for row in results:
        table.append([format_value(row.get(c)) for c in columns])
    widths = [max(len(line[i]) for line in table) for i in range(len(columns))]
    return (
        "\n".join(
            "  ".join(cell.ljust(w) for cell, w in zip(line, widths)).rstrip()
            for line in table
        )
        + "\n"
    )


def csv_output(results: list[dict], swept: list[str]) -> str:
    columns = result_columns(results, swept)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in results:
        writer.writerow([format_value(row.get(c)) for c in columns])
    return buffer.getvalue()


def json_output(
    results: list[dict],
    best: dict,
    metadata: dict,
) -> str:
    document = dict(metadata)
    document["results"] = results
    document["best"] = best
    return json.dumps(document, indent=4) + "\n"


def set_deviations_colors(map_name: str, data_type: str) -> None:
    """Set a diverging color scheme centered on the residual quartiles"""
    try:
        stats = gs.parse_command("r.univar", map=map_name, flags="ge", quiet=True)
        color_scheme = "\n".join(
            [
                f"{stats['min']} red",
                f"{stats['first_quartile']} yellow",
                f"{stats['median']} 220:220:220",
                f"{stats['third_quartile']} cyan",
                f"{stats['max']} blue",
            ]
        )
    except (CalledModuleError, KeyError) as error:
        gs.warning(
            _("Unable to set colors for <{name}>: {error}").format(
                name=map_name, error=error
            )
        )
        return

    if data_type == "raster":
        gs.write_command(
            "r.colors", map=map_name, rules="-", stdin=color_scheme, quiet=True
        )
    elif data_type == "vector":
        gs.write_command(
            "v.colors",
            map=map_name,
            rules="-",
            use="attr",
            column="flt1",
            stdin=color_scheme,
            quiet=True,
        )


def compute_deviation_surfaces(results: list[dict]) -> None:
    """Interpolate saved cross-validation residuals into deviation surfaces"""
    gs.message(_("Computing deviation surfaces..."))
    for row in results:
        if row["error"] is not None or not row["cvdev"]:
            continue
        args = {
            key: row[key]
            for key in ("tension", "smooth", "npmin", "segmax")
            if row.get(key) is not None
        }
        try:
            gs.run_command(
                "v.surf.rst",
                input=row["cvdev"],
                elevation=row["cvdev"],
                zcolumn="flt1",
                quiet=True,
                overwrite=True,
                **args,
            )
        except CalledModuleError as error:
            gs.warning(
                _("Error computing deviation surface for <{name}>: {error}").format(
                    name=row["cvdev"], error=error
                )
            )
            continue
        set_deviations_colors(row["cvdev"], "vector")
        set_deviations_colors(row["cvdev"], "raster")


def emit_selection_warnings(
    results: list[dict], best: dict, swept: list[str]
) -> list[str]:
    """Warn about failed runs, incomparable samples, and metric disagreement"""
    warnings = []
    failed = [r for r in results if r["error"] is not None]
    if failed:
        warnings.append(
            _(
                "{count} parameter combinations failed; the search grid is incomplete"
            ).format(count=len(failed))
        )
    ok = [r for r in results if r["error"] is None]
    if ok and ("dmin" in swept or "dmax" in swept) and len({r["n"] for r in ok}) > 1:
        warnings.append(
            _(
                "dmin/dmax values changed the number of cross-validated points "
                "(see the n column); error metrics are not directly comparable "
                "across those rows"
            )
        )
    if best:
        picks = {
            metric: (best[metric]["tension"], best[metric]["smooth"])
            for metric in METRIC_KEYS
        }
        if len(set(picks.values())) > 1:
            warnings.append(
                _(
                    "Best parameters differ between metrics ({picks}); the selection "
                    "is sensitive to outliers, inspect the residual distribution"
                ).format(
                    picks=", ".join(
                        f"{m}: tension={format_value(p[0])} smooth={format_value(p[1])}"
                        for m, p in picks.items()
                    )
                )
            )
    for warning in warnings:
        gs.warning(warning)
    return warnings


def main():
    points = options["point_cloud"]
    output_file = options["output_file"]
    output_format = options["format"]
    method = options["method"]
    levels = int(options["levels"])
    cv_prefix = options["cv_prefix"] or None
    zscale = float(options["zscale"]) if options["zscale"] else 1.0
    workers = max(1, int(options["nprocs"]))
    scale_dependent = flags["t"]

    tension_list = parse_number_list(options["tension"], "tension")
    smooth_list = parse_number_list(options["smooth"], "smooth")
    if not tension_list or not smooth_list:
        gs.fatal(_("Options tension and smooth require at least one value each."))
    if levels < 1:
        gs.fatal(_("Option levels must be at least 1."))
    structural_values = {
        param: parse_number_list(options[param], param)
        for param in STRUCTURAL_PARAMS
        if options[param]
    }
    swept = list(structural_values)

    if options["scalex"] and not options["theta"]:
        gs.fatal(_("Using anisotropy requires both theta and scalex options."))
    if options["theta"] or options["scalex"]:
        gs.warning(
            _(
                "v.surf.rst evaluates cross-validation residuals without applying "
                "the anisotropy transformation used in the interpolation; "
                "cross-validation errors with theta/scalex are unreliable "
                "until this is fixed in GRASS."
            )
        )
    if len(structural_values.get("npmin", [])) > 1 and not scale_dependent:
        gs.warning(
            _(
                "npmin rescales the internal normalization factor (dnorm), which "
                "changes the effective tension; use the -t flag to compare "
                "tension values across npmin settings."
            )
        )
    if options["seed"] and not options["npoints"]:
        gs.warning(_("Option seed has no effect without the npoints option."))

    # Pass-through arguments identical for every run
    base_args = {
        key: options[key]
        for key in ("layer", "zcolumn", "where", "mask")
        if options[key]
    }
    if options["zscale"]:
        base_args["zscale"] = zscale

    bbox = gs.parse_command("v.info", map=points, flags="g")
    bbox = {k: float(bbox[k]) for k in ("north", "south", "east", "west")}

    if options["npoints"]:
        if not scale_dependent:
            gs.warning(
                _(
                    "Tuning tension on a subsample without the -t flag: the optimal "
                    "tension shifts with point density and will not transfer to the "
                    "full data set."
                )
            )
        seed = int(options["seed"]) if options["seed"] else None
        points = spatial_subsample(
            points, options["layer"], int(options["npoints"]), seed, bbox
        )
        if points != options["point_cloud"]:
            bbox = gs.parse_command("v.info", map=points, flags="g")
            bbox = {k: float(bbox[k]) for k in ("north", "south", "east", "west")}

    dnorm_area = (bbox["east"] - bbox["west"]) * (bbox["north"] - bbox["south"])

    if cv_prefix and not gs.overwrite():
        existing = gs.read_command(
            "g.list",
            type="vector,raster",
            pattern=f"{cv_prefix}_*",
            mapset=".",
            quiet=True,
        ).split()
        if existing:
            gs.fatal(
                _(
                    "Maps with prefix <{prefix}> already exist ({first} ...); "
                    "use --overwrite or another cv_prefix"
                ).format(prefix=cv_prefix, first=existing[0])
            )

    validator = CrossValidator(
        points=points,
        base_args=base_args,
        scale_dependent=scale_dependent,
        zscale=zscale,
        cv_prefix=cv_prefix,
        workers=workers,
        dnorm_area=dnorm_area,
    )

    structural_combos = [
        dict(zip(structural_values.keys(), combo))
        for combo in itertools.product(*structural_values.values())
    ] or [{}]

    total = len(tension_list) * len(smooth_list) * len(structural_combos)
    if method == "refine":
        gs.message(
            _(
                "Cross-validating {total} initial parameter combinations "
                "(refine search adds more per level)"
            ).format(total=total)
        )
    else:
        gs.message(
            _("Cross-validating {total} parameter combinations (grid search)").format(
                total=total
            )
        )
    if total > RUN_COUNT_WARNING:
        gs.warning(
            _(
                "{total} cross-validation runs requested; consider narrowing the "
                "parameter lists or using method=refine."
            ).format(total=total)
        )

    if method == "refine":
        for structural in structural_combos:
            refine_search(validator, tension_list, smooth_list, structural, levels)
    else:
        combos = [
            dict(structural, tension=t, smooth=s)
            for structural in structural_combos
            for t, s in itertools.product(tension_list, smooth_list)
        ]
        validator.run_batch(combos)

    results = validator.results
    best = best_rows(results)
    warnings = emit_selection_warnings(results, best, swept)

    if best:
        row = best["rmse"]
        gs.message(_("Best parameter combination (by RMSE)"))
        gs.message("-" * 50)
        gs.message(_("Tension: {}").format(format_value(row["tension"])))
        gs.message(_("Smoothing: {}").format(format_value(row["smooth"])))
        for param in swept:
            gs.message(f"{param}: {format_value(row.get(param))}")
        gs.message(_("RMSE: {}").format(format_value(row["rmse"])))
        gs.message(_("MAE: {}").format(format_value(row["mae"])))
        gs.message(_("NMAD: {}").format(format_value(row["nmad"])))
        gs.message("-" * 50)
    else:
        gs.warning(
            _("No results found. Unable to determine the best parameter combination.")
        )

    if cv_prefix:
        compute_deviation_surfaces(results)

    if output_format == "json":
        region = gs.region()
        metadata = {
            "input": options["point_cloud"],
            "method": method,
            "scale_dependent_tension": scale_dependent,
            "subsample": (
                {
                    "npoints": int(options["npoints"]),
                    "seed": int(options["seed"]) if options["seed"] else None,
                }
                if options["npoints"]
                else None
            ),
            "region": {
                key: region[key]
                for key in ("n", "s", "e", "w", "nsres", "ewres", "rows", "cols")
            },
            "warnings": warnings,
        }
        output = json_output(results, best, metadata)
    elif output_format == "csv":
        output = csv_output(results, swept)
    else:
        output = plain_output(results, swept)

    sys.stdout.write(output)
    if output_file:
        try:
            Path(output_file).write_text(output, encoding="utf-8")
            gs.message(_("Results written to '{}'").format(output_file))
        except OSError as error:
            gs.fatal(_("Error writing output file: {}").format(error))

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
