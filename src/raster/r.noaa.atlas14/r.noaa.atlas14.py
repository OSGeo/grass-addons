#!/usr/bin/env python

##############################################################################
# MODULE:    r.noaa.atlas14
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Import NOAA Atlas 14 precipitation-frequency data from PFDS point
#            queries or official GIS-compatible grid downloads.
#
# COPYRIGHT: (C) 2026 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""
Import NOAA Atlas 14 precipitation-frequency data from
PFDS point queries or official GIS-compatible grid downloads.
"""

# %module
# % description: Downloads and imports NOAA Atlas 14 precipitation-frequency data from the PFDS point service or official GIS grid packages.
# % keyword: raster
# % keyword: hydrology
# % keyword: precipitation
# % keyword: vector
# % keyword: rainfall
# % keyword: NOAA
# % keyword: Atlas 14
# %end

# %option
# % key: mode
# % type: string
# % required: yes
# % options: point,grid
# % description: Data acquisition mode
# % guisection: General
# %end

# %option
# % key: statistic
# % type: string
# % required: no
# % options: depth,intensity
# % answer: depth
# % description: Statistic to request/import
# % guisection: General
# %end

# %option
# % key: units
# % type: string
# % required: no
# % options: english,metric
# % answer: english
# % description: Units for point queries or for filtering grids
# % guisection: General
# %end

# %option
# % key: series
# % type: string
# % required: no
# % options: pds,ams
# % answer: pds
# % description: Time series type for point queries or for filtering grids
# % guisection: General
# %end

# %option
# % key: bound
# % type: string
# % required: no
# % options: expected,upper,lower,all
# % answer: expected
# % description: Bound to return/import
# % guisection: General
# %end

# %option G_OPT_M_COORDS
# % multiple: yes
# % required: no
# % key_desc: lon,lat
# % description: Longitude,Latitude pair(s) in decimal degrees for mode=point; if omitted, the center of the computational region is used
# % guisection: Point
# %end

# %option G_OPT_V_OUTPUT
# % key: vector_output
# % required: no
# % description: Optional output vector point map for mode=point
# % guisection: Point
# %end

# %option
# % key: output
# % type: string
# % required: no
# % description: Optional path for point output file (.json or .csv) or grid manifest CSV
# % guisection: Output
# %end

# %option
# % key: format
# % type: string
# % required: no
# % options: json,csv
# % answer: json
# % description: Output format for mode=point
# % guisection: Output
# %end

# %option
# % key: float_format
# % type: string
# % required: no
# % answer: .3f
# % description: Python format string for CSV numeric output in mode=point
# % guisection: Output
# %end

# %option
# % key: region
# % type: string
# % required: no
# % description: Atlas 14 grid region code, e.g. sw, orb, pr, hi, nmi, ch, ko, pp, nk, pg, yp, wl, ul, pl, rm, as, gu, wki, ak, mw, se, ne, tx, inw
# % guisection: Grid
# %end

# %option
# % key: archive_url
# % type: string
# % required: no
# % description: Direct URL to a NOAA grid ZIP archive or a directory listing page; overrides autodiscovery in mode=grid
# % guisection: Grid
# %end

# %option
# % key: durations
# % type: string
# % multiple: yes
# % required: no
# % description: Duration filters for mode=grid, e.g. 5min,10min,24hr,2day
# % guisection: Grid
# %end

# %option
# % key: aris
# % type: integer
# % multiple: yes
# % required: no
# % description: Average recurrence intervals in years for mode=grid, e.g. 2,10,100
# % guisection: Grid
# %end

# %option
# % key: output_prefix
# % type: string
# % required: no
# % answer: a14
# % description: Prefix for imported raster names in mode=grid
# % guisection: Grid
# %end

# %option G_OPT_R_INTERP_TYPE
# % key: resample
# % type: string
# % required: no
# % options: nearest,bilinear,bicubic,lanczos
# % answer: nearest
# % description: Resampling method used by r.import in mode=grid
# % guisection: Grid
# %end

# %option
# % key: base_gis_url
# % type: string
# % required: no
# % answer: https://hdsc.nws.noaa.gov/pub/hdsc/data
# % description: Base HTTPS directory for NOAA Atlas 14 GIS data; used for grid autodiscovery
# % guisection: Grid
# %end

# %option
# % key: separator
# % type: string
# % required: no
# % options: comma,pipe,tab,space
# % answer: comma
# % description: Separator for CSV-like outputs where relevant
# % guisection: Output
# %end

# %flag
# % key: l
# % description: List matching grid archives and exit (mode=grid)
# % guisection: Grid
# %end

# %flag
# % key: k
# % description: Keep downloaded archives and unpacked files
# % guisection: Grid
# %end

# %flag
# % key: c
# % description: Print point result to stdout even if output file is written
# % guisection: Output
# %end

# %flag
# % key: i
# % description: Use r.import instead of r.in.gdal for grid import
# % guisection: Grid
# %end

# %flag
# % key: o
# % description: Override projection check when using r.in.gdal
# % guisection: Grid
# %end
from __future__ import annotations
import csv
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any, Iterable, Literal
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import grass.script as gs

PFDS_POINT_URL = "https://hdsc.nws.noaa.gov/cgi-bin/new/fe_text.csv"
USER_AGENT = "Mozilla/5.0 (compatible; r.noaa.atlas14/0.1)"

REGION_INFO = {
    "sw": "Volume 1 Semiarid Southwest / Volume 6 California",
    "orb": "Volume 2 Ohio River Basin and Surrounding States",
    "pr": "Volume 3 Puerto Rico and U.S. Virgin Islands",
    "hi": "Volume 4 Hawaiian Islands",
    "nmi": "Volume 5 Northern Mariana Islands",
    "ch": "Volume 5 Chuuk",
    "ko": "Volume 5 Kosrae",
    "pp": "Volume 5 Pohnpei",
    "nk": "Volume 5 Nukuoro",
    "pg": "Volume 5 Pingelap",
    "yp": "Volume 5 Yap Islands",
    "wl": "Volume 5 Woleai",
    "ul": "Volume 5 Ulithi",
    "pl": "Volume 5 Palau",
    "rm": "Volume 5 Marshall Islands",
    "as": "Volume 5 American Samoa",
    "gu": "Volume 5 Guam",
    "wki": "Volume 5 Wake Island",
    "ak": "Volume 7 Alaska",
    "mw": "Volume 8 Midwestern States",
    "se": "Volume 9 Southeastern States",
    "ne": "Volume 10 Northeastern States",
    "tx": "Volume 11 Texas",
    "inw": "Volume 12 Interior Northwest",
}

BOUND_LABELS = {
    "expected": "expected",
    "upper": "upper",
    "lower": "lower",
}

DURATION_ALIASES = {
    "5-minute": "5min",
    "10-minute": "10min",
    "15-minute": "15min",
    "30-minute": "30min",
    "60-minute": "60min",
    "2-hour": "2hr",
    "3-hour": "3hr",
    "6-hour": "6hr",
    "12-hour": "12hr",
    "24-hour": "24hr",
    "2-day": "2day",
    "3-day": "3day",
    "4-day": "4day",
    "7-day": "7day",
    "10-day": "10day",
    "20-day": "20day",
    "30-day": "30day",
    "45-day": "45day",
    "60-day": "60day",
}


class Atlas14Error(Exception):
    pass


@dataclass
class GridCandidate:
    url: str
    filename: str
    region: str | None = None
    bound: str | None = None
    statistic: str | None = None
    units: str | None = None
    series: str | None = None
    duration: str | None = None
    ari: int | None = None


def http_get_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_download(url: str, dst: Path) -> None:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as resp, open(dst, "wb") as f:
        shutil.copyfileobj(resp, f)


def parse_pfds_response(
    text: str, request: dict[str, Any] | None = None
) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise Atlas14Error("Empty PFDS response")

    result: dict[str, Any] = {
        "request": request or {},
        "metadata": {},
        "tables": {
            "expected": {"return_periods_years": [], "rows": []},
            "upper": {"return_periods_years": [], "rows": []},
            "lower": {"return_periods_years": [], "rows": []},
        },
    }

    current_section = "expected"
    current_rps: list[int | float | str] | None = None

    for line in lines:
        low = line.lower()

        if "upper bound of 90% confidence interval" in low:
            current_section = "upper"
            current_rps = None
            continue
        if "lower bound of 90% confidence interval" in low:
            current_section = "lower"
            current_rps = None
            continue
        if low.startswith("date/time") or low.startswith("pyruntime"):
            continue

        if current_section == "expected" and current_rps is None:
            m = re.match(r"^\s*([^=,:]+?)\s*[:=]\s*(.+?)\s*$", line)
            if m and not low.startswith("by duration for ari"):
                key = re.sub(r"\s+", "_", m.group(1).strip().lower())
                result["metadata"][key] = m.group(2).strip()

        if low.startswith("by duration for ari"):
            row = next(csv.reader([line]))
            current_rps = [_parse_numeric_label(x) for x in row[1:]]
            result["tables"][current_section]["return_periods_years"] = current_rps
            continue

        if current_rps is None:
            continue

        row = next(csv.reader([line]))
        if len(row) < 2:
            continue

        duration = row[0].strip().rstrip(":")
        if not duration:
            continue
        if duration.lower().startswith("precipitation frequency estimates"):
            continue

        values: dict[str, float | str | None] = {}
        numeric_count = 0
        for rp, cell in zip(current_rps, row[1:]):
            key = str(rp)
            cell = cell.strip()
            if cell in {"", "-", "--", "---"}:
                values[key] = None
                continue
            try:
                values[key] = float(cell)
                numeric_count += 1
            except ValueError:
                values[key] = cell

        if numeric_count == 0:
            continue

        result["tables"][current_section]["rows"].append(
            {
                "duration": duration,
                "values": values,
            }
        )

    if not result["tables"]["expected"]["rows"]:
        raise Atlas14Error("No PFDS expected-value rows were parsed")

    return result


def fetch_pfds_point(
    lat: float, lon: float, statistic: str, units: str, series: str
) -> dict[str, Any]:
    import urllib.parse

    params = urllib.parse.urlencode(
        {
            "lat": lat,
            "lon": lon,
            "data": statistic,
            "units": units,
            "series": series,
        }
    )
    url = f"{PFDS_POINT_URL}?{params}"
    text = http_get_text(url)
    return parse_pfds_response(
        text,
        request={
            "lat": lat,
            "lon": lon,
            "statistic": statistic,
            "units": units,
            "series": series,
            "url": url,
        },
    )


def pfds_to_csv_text(data: dict[str, Any], bound: str, float_format: str) -> str:
    if bound == "all":
        parts = []
        for section in ("expected", "upper", "lower"):
            parts.append(f"# {section}")
            parts.append(pfds_to_csv_text(data, section, float_format).rstrip())
            parts.append("")
        return "\n".join(parts).rstrip() + "\n"

    table = data["tables"][bound]
    rps = table["return_periods_years"]
    rows = table["rows"]
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["duration"] + [_format_rp(x) for x in rps])
    for row in rows:
        vals = [row["duration"]]
        for rp in rps:
            value = row["values"].get(str(rp))
            if value is None:
                vals.append("")
            elif isinstance(value, float):
                vals.append(format(value, float_format))
            else:
                vals.append(str(value))
        writer.writerow(vals)
    return out.getvalue()


def _single_point_json_payload(data: dict[str, Any], bound: str) -> dict[str, Any]:
    if bound == "all":
        return data
    return {
        "request": data["request"],
        "metadata": data["metadata"],
        "bound": bound,
        "table": data["tables"][bound],
    }


def _pfds_to_csv_rows_with_coords(
    data: dict[str, Any], bound: str, float_format: str, lon: float, lat: float
) -> list[list[str]]:
    """CSV rows for a single point with lon,lat prepended; no header row."""
    sections = ("expected", "upper", "lower") if bound == "all" else (bound,)
    rows: list[list[str]] = []
    for section in sections:
        table = data["tables"][section]
        rps = table["return_periods_years"]
        for row in table["rows"]:
            values = [
                f"{lon}",
                f"{lat}",
                section if bound == "all" else bound,
                row["duration"],
            ]
            for rp in rps:
                v = row["values"].get(str(rp))
                if v is None:
                    values.append("")
                elif isinstance(v, float):
                    values.append(format(v, float_format))
                else:
                    values.append(str(v))
            rows.append(values)
    return rows


def _multi_point_csv_text(
    results: list[dict[str, Any]], bound: str, float_format: str
) -> str:
    """Combined CSV over multiple points. Assumes all points share the same
    return-period header (NOAA PFDS returns the same RPs for all lat/lon)."""
    first = results[0]
    first_section = "expected" if bound == "all" else bound
    rps = first["tables"][first_section]["return_periods_years"]
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["lon", "lat", "bound", "duration"] + [_format_rp(x) for x in rps])
    for data in results:
        lon = data["request"]["lon"]
        lat = data["request"]["lat"]
        for row in _pfds_to_csv_rows_with_coords(data, bound, float_format, lon, lat):
            writer.writerow(row)
    return out.getvalue()


def write_point_output(
    results: list[dict[str, Any]],
    fmt: str,
    bound: str,
    output: str | None,
    float_format: str,
    *,
    print_stdout: bool,
) -> None:
    multi = len(results) > 1
    if fmt == "json":
        if multi:
            payload: Any = [_single_point_json_payload(d, bound) for d in results]
        else:
            payload = _single_point_json_payload(results[0], bound)
        text = json.dumps(payload, indent=2)
    else:
        if multi:
            text = _multi_point_csv_text(results, bound, float_format)
        else:
            text = pfds_to_csv_text(results[0], bound, float_format)

    if output:
        Path(output).write_text(text, encoding="utf-8")
        gs.message(f"Wrote {fmt.upper()} output to {output}")
    if print_stdout or not output:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def create_point_vector(
    mapname: str, points: list[tuple[float, float, dict[str, Any]]]
) -> None:
    tmpdir = Path(tempfile.mkdtemp(prefix="atlas14_point_"))
    try:
        ascii_path = tmpdir / "points.csv"
        with ascii_path.open("w", encoding="utf-8") as f:
            for cat, (lon, lat, _) in enumerate(points, start=1):
                f.write(f"{cat}|{lon}|{lat}\n")

        gs.run_command(
            "v.in.ascii",
            input=str(ascii_path),
            output=mapname,
            separator="pipe",
            x=2,
            y=3,
            cat=1,
            format="point",
            overwrite=gs.overwrite(),
        )
        gs.run_command(
            "v.db.addtable",
            map=mapname,
            columns="lon double precision, lat double precision, expected_json text, upper_json text, lower_json text",
        )
        for cat, (lon, lat, data) in enumerate(points, start=1):
            gs.run_command(
                "db.execute",
                sql=(
                    f"UPDATE {mapname} SET lon = {lon}, lat = {lat}, "
                    f"expected_json = '{_sql_escape(json.dumps(data['tables']['expected']))}', "
                    f"upper_json = '{_sql_escape(json.dumps(data['tables']['upper']))}', "
                    f"lower_json = '{_sql_escape(json.dumps(data['tables']['lower']))}' "
                    f"WHERE cat = {cat}"
                ),
            )
        gs.message(
            f"Created vector point map <{mapname}> with {len(points)} point(s) "
            "and JSON attributes"
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def discover_grid_archives(base_url: str, region: str) -> list[GridCandidate]:
    """
    Discover ZIP archives from NOAA HTTPS directory listing.

    This is necessarily heuristic because NOAA naming conventions vary across
    archives/volumes. Users can override with archive_url= if needed.
    """
    html = http_get_text(base_url.rstrip("/") + "/")
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    candidates: list[GridCandidate] = []
    for href in hrefs:
        link = unescape(href)
        if not link.lower().endswith(".zip"):
            continue
        url = urljoin(base_url.rstrip("/") + "/", link)
        filename = os.path.basename(urlparse(url).path)
        if region and region.lower() not in filename.lower():
            continue
        meta = parse_grid_filename(filename)
        meta.url = url
        candidates.append(meta)
    return candidates


def parse_grid_filename(filename: str) -> GridCandidate:
    name = filename.lower()
    region = next(
        (
            r
            for r in REGION_INFO
            if re.search(rf"(?:^|[_\-]){re.escape(r)}(?:[_\-.]|$)", name)
        ),
        None,
    )

    if any(tok in name for tok in ["upper", "upl", "u90"]):
        bound = "upper"
    elif any(tok in name for tok in ["lower", "lwr", "low", "l90"]):
        bound = "lower"
    else:
        bound = "expected"

    statistic = None
    if "intensity" in name or re.search(r"(?:^|[_\-])i(?:[_\-.]|$)", name):
        statistic = "intensity"
    elif "depth" in name or re.search(r"(?:^|[_\-])d(?:[_\-.]|$)", name):
        statistic = "depth"

    units = None
    if "metric" in name:
        units = "metric"
    elif "english" in name or "inch" in name:
        units = "english"

    series = None
    if "pds" in name:
        series = "pds"
    elif "ams" in name:
        series = "ams"

    duration = None
    duration_patterns = [
        (r"5[\-_]?min", "5min"),
        (r"10[\-_]?min", "10min"),
        (r"15[\-_]?min", "15min"),
        (r"30[\-_]?min", "30min"),
        (r"60[\-_]?min", "60min"),
        (r"2[\-_]?(?:hr|hour)", "2hr"),
        (r"3[\-_]?(?:hr|hour)", "3hr"),
        (r"6[\-_]?(?:hr|hour)", "6hr"),
        (r"12[\-_]?(?:hr|hour)", "12hr"),
        (r"24[\-_]?(?:hr|hour)", "24hr"),
        (r"2[\-_]?day", "2day"),
        (r"3[\-_]?day", "3day"),
        (r"4[\-_]?day", "4day"),
        (r"7[\-_]?day", "7day"),
        (r"10[\-_]?day", "10day"),
        (r"20[\-_]?day", "20day"),
        (r"30[\-_]?day", "30day"),
        (r"45[\-_]?day", "45day"),
        (r"60[\-_]?day", "60day"),
    ]
    for pat, norm in duration_patterns:
        if re.search(pat, name):
            duration = norm
            break

    ari = None
    m = re.search(r"(?:^|[_\-])(\d{1,4})[\-_]?(?:yr|year|ari)(?:[_\-.]|$)", name)
    if not m:
        m = re.search(r"ari[\-_]?(\d{1,4})", name)
    if m:
        ari = int(m.group(1))

    return GridCandidate(
        url="",
        filename=filename,
        region=region,
        bound=bound,
        statistic=statistic,
        units=units,
        series=series,
        duration=duration,
        ari=ari,
    )


def filter_candidates(
    candidates: Iterable[GridCandidate],
    bound: str,
    statistic: str | None,
    units: str | None,
    series: str | None,
    durations: set[str] | None,
    aris: set[int] | None,
) -> list[GridCandidate]:
    # bound/statistic/units/series carry parser defaults that NOAA filenames
    # don't always encode, so candidates with None for those attributes are
    # allowed through (permissive match). durations and aris are only set
    # when the user explicitly lists them, so those filters are strict —
    # a candidate whose ARI or duration couldn't be parsed is rejected.
    out = []
    for c in candidates:
        if bound != "all" and c.bound is not None and c.bound != bound:
            continue
        if statistic and c.statistic is not None and c.statistic != statistic:
            continue
        if units and c.units is not None and c.units != units:
            continue
        if series and c.series is not None and c.series != series:
            continue
        if durations is not None and c.duration not in durations:
            continue
        if aris is not None and c.ari not in aris:
            continue
        out.append(c)
    return out


def _safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    dest_resolved = dest.resolve()
    for member in zf.infolist():
        target = (dest / member.filename).resolve()
        try:
            target.relative_to(dest_resolved)
        except ValueError:
            raise Atlas14Error(
                f"Refusing to extract archive member outside destination: {member.filename!r}"
            )
    zf.extractall(dest)


def import_zip_archive(
    archive_path: Path,
    output_prefix: str,
    resample: str,
    manifest_rows: list[dict[str, Any]],
    *,
    use_r_import: bool,
    override_proj: bool,
) -> None:
    tmp_extract = Path(tempfile.mkdtemp(prefix="atlas14_unzip_"))
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            _safe_extract_zip(zf, tmp_extract)

        raster_files = []
        for root, _, files in os.walk(tmp_extract):
            for f in files:
                lower = f.lower()
                if lower.endswith((".asc", ".tif", ".tiff", ".adf")):
                    raster_files.append(Path(root) / f)

        if not raster_files:
            gs.warning(f"No raster files found in {archive_path.name}")
            return

        for raster in raster_files:
            meta = parse_grid_filename(raster.name)
            outname = build_raster_name(output_prefix, meta, raster.stem)
            gs.message(f"Importing {raster.name} -> {outname}")
            if use_r_import:
                gs.run_command(
                    "r.import",
                    input=str(raster),
                    output=outname,
                    resample=resample,
                    overwrite=gs.overwrite(),
                )
                # save history into the output raster
                gs.raster_history(outname, overwrite=True)
            else:
                kwargs = {
                    "input": str(raster),
                    "output": outname,
                    "overwrite": gs.overwrite(),
                }
                if override_proj:
                    kwargs["flags"] = "o"
                gs.run_command("r.in.gdal", **kwargs)

            history = json.dumps(
                {
                    "source_archive": archive_path.name,
                    "source_file": raster.name,
                    "parsed": meta.__dict__,
                }
            )
            try:
                gs.run_command("r.support", map=outname, history=history)
            except Exception:
                pass

            manifest_rows.append(
                {
                    "map": outname,
                    "source_archive": archive_path.name,
                    "source_file": raster.name,
                    "region": meta.region,
                    "bound": meta.bound,
                    "statistic": meta.statistic,
                    "units": meta.units,
                    "series": meta.series,
                    "duration": meta.duration,
                    "ari": meta.ari,
                }
            )
    finally:
        shutil.rmtree(tmp_extract, ignore_errors=True)


def build_raster_name(prefix: str, meta: GridCandidate, fallback_stem: str) -> str:
    parts = [prefix]
    if meta.statistic:
        parts.append(meta.statistic)
    if meta.bound:
        parts.append(meta.bound)
    if meta.duration:
        parts.append(meta.duration)
    if meta.ari is not None:
        parts.append(f"{meta.ari}yr")
    if meta.units:
        parts.append(meta.units)
    if meta.series:
        parts.append(meta.series)
    if meta.region:
        parts.append(meta.region)
    if len(parts) == 1:
        parts.append(sanitize_name(fallback_stem))
    return sanitize_name("_".join(parts))


def write_manifest(rows: list[dict[str, Any]], path: str) -> None:
    if not rows:
        return
    fieldnames = [
        "map",
        "source_archive",
        "source_file",
        "region",
        "bound",
        "statistic",
        "units",
        "series",
        "duration",
        "ari",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    gs.message(f"Wrote grid import manifest to {path}")


def normalize_duration(value: str) -> str:
    v = value.strip().lower().replace("-", "").replace("_", "")
    return DURATION_ALIASES.get(value.strip().lower(), v)


def sanitize_name(name: str) -> str:
    n = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    n = re.sub(r"_+", "_", n).strip("_")
    return n[:63]


def _parse_numeric_label(value: str) -> int | float | str:
    value = value.strip()
    try:
        n = float(value)
        return int(n) if n.is_integer() else n
    except ValueError:
        return value


def _format_rp(value: float | str) -> str:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else format(value, "g")
    return str(value)


def _sql_escape(value: str) -> str:
    return value.replace("'", "''")


def parse_coordinates(coords_str: str) -> list[tuple[float, float]]:
    """Parse a G_OPT_M_COORDS value into a list of (lon, lat) pairs."""
    parts = [x.strip() for x in coords_str.split(",") if x.strip()]
    if not parts:
        return []
    if len(parts) % 2 != 0:
        raise Atlas14Error("coordinates must be supplied as one or more lon,lat pairs")
    try:
        values = [float(p) for p in parts]
    except ValueError as exc:
        raise Atlas14Error(f"Invalid coordinate value: {exc}") from exc
    return list(zip(values[0::2], values[1::2]))


def region_center_lonlat() -> tuple[float, float]:
    """Return the computational region center in WGS84 lon/lat.

    g.region -b computes the lat/lon bounds of the current region regardless
    of the native CRS; in a lat/lon location the native n/s/e/w values are
    used as a fallback.
    """
    try:
        info = gs.parse_command("g.region", flags="bg")
    except Exception as exc:
        raise Atlas14Error(
            f"Could not determine computational region center: {exc}"
        ) from exc

    def _pick(*keys: str) -> float | None:
        for k in keys:
            if k in info:
                try:
                    return float(info[k])
                except (TypeError, ValueError):
                    return None
        return None

    n = _pick("ll_n", "n")
    s = _pick("ll_s", "s")
    e = _pick("ll_e", "e")
    w = _pick("ll_w", "w")
    if None in (n, s, e, w):
        raise Atlas14Error(
            "Could not parse region bounds as lon/lat from g.region output"
        )
    return ((w + e) / 2.0, (n + s) / 2.0)


def run_point_mode(options: dict[str, str], flags: dict[str, bool]) -> None:
    coords_str = options["coordinates"]
    if coords_str:
        points = parse_coordinates(coords_str)
    else:
        lon, lat = region_center_lonlat()
        gs.message(
            f"No coordinates given; using computational region center: "
            f"lon={lon:.6f}, lat={lat:.6f}"
        )
        points = [(lon, lat)]

    results: list[dict[str, Any]] = []
    vector_points: list[tuple[float, float, dict[str, Any]]] = []
    for lon, lat in points:
        gs.message(f"Querying PFDS for lon={lon}, lat={lat}")
        data = fetch_pfds_point(
            lat=lat,
            lon=lon,
            statistic=options["statistic"],
            units=options["units"],
            series=options["series"],
        )
        results.append(data)
        vector_points.append((lon, lat, data))

    write_point_output(
        results=results,
        fmt=options["format"],
        bound=options["bound"],
        output=options["output"] or None,
        print_stdout=flags["c"],
        float_format=options["float_format"],
    )

    if options["vector_output"]:
        create_point_vector(options["vector_output"], vector_points)


def resolve_archive_candidates(options: dict[str, str]) -> list[GridCandidate]:
    archive_url = options["archive_url"]
    region = (options["region"] or "").strip().lower()
    if not region and not archive_url:
        gs.fatal("region= is required for mode=grid unless archive_url= is provided")

    if archive_url:
        if archive_url.lower().endswith(".zip"):
            c = parse_grid_filename(os.path.basename(urlparse(archive_url).path))
            c.url = archive_url
            return [c]
        return discover_grid_archives(archive_url, region)

    return discover_grid_archives(options["base_gis_url"], region)


def run_grid_mode(options: dict[str, str], flags: dict[str, bool]) -> None:
    durations = None
    if options["durations"]:
        durations = {
            normalize_duration(x) for x in options["durations"].split(",") if x.strip()
        }
    aris = None
    if options["aris"]:
        aris = {int(x) for x in options["aris"].split(",") if x.strip()}

    candidates = resolve_archive_candidates(options)
    if not candidates:
        gs.fatal(
            "No candidate grid archives found. Try archive_url= with a direct NOAA ZIP link."
        )

    filtered = filter_candidates(
        candidates,
        bound=options["bound"],
        statistic=options["statistic"],
        units=options["units"],
        series=options["series"],
        durations=durations,
        aris=aris,
    )

    if flags["l"]:
        if not filtered:
            gs.message("No matching archives found")
            return
        for c in filtered:
            sys.stdout.write(json.dumps(c.__dict__) + "\n")
        return

    if not filtered:
        gs.fatal("No grid archives matched the supplied filters")

    workdir = Path(tempfile.mkdtemp(prefix="atlas14_grid_"))
    manifest_rows: list[dict[str, Any]] = []
    try:
        for c in filtered:
            dst = workdir / c.filename
            gs.message(f"Downloading {c.url}")
            http_download(c.url, dst)
            import_zip_archive(
                archive_path=dst,
                output_prefix=options["output_prefix"],
                resample=options["resample"],
                use_r_import=flags["i"],
                override_proj=flags["o"],
                manifest_rows=manifest_rows,
            )
            if flags["k"]:
                gs.message(f"Kept archive at {dst}")
            else:
                try:
                    dst.unlink()
                except FileNotFoundError:
                    pass

        if options["output"]:
            write_manifest(manifest_rows, options["output"])
        else:
            gs.message(f"Imported {len(manifest_rows)} raster(s)")
    finally:
        if flags["k"]:
            gs.message(f"Temporary grid download directory retained: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    options, flags = gs.parser()
    try:
        if options["mode"] == "point":
            run_point_mode(options, flags)
        elif options["mode"] == "grid":
            run_grid_mode(options, flags)
        else:
            gs.fatal("Unsupported mode")
        return 0
    except Atlas14Error as e:
        gs.fatal(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
