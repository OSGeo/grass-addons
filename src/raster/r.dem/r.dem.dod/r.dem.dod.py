#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.dod
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Compute a DEM of Difference (DoD) on the computational region,
#            resampling misaligned inputs, with the r.dem erosion and
#            deposition palette, source metadata, and timestamps.
#
# SPDX-FileCopyrightText: 2026 Corey T. White
# SPDX-FileCopyrightText: GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Computes a DEM of Difference (DoD)
# % keyword: raster
# % keyword: DEM
# % keyword: change detection
# % keyword: geomorphology
# % keyword: elevation
# %end

# %option G_OPT_R_INPUT
# % key: dem
# % description: Later DEM
# %end

# %option G_OPT_R_INPUT
# % key: reference
# % description: Earlier reference DEM
# %end

# %option G_OPT_R_OUTPUT
# % description: DEM of Difference
# %end

# %option
# % key: interp
# % type: string
# % required: no
# % options: bilinear,bicubic
# % answer: bilinear
# % description: Interpolation for inputs not aligned with the computational region
# %end

# %option
# % key: range
# % type: double
# % required: no
# % label: Absolute difference at which the color palette saturates
# % description: Default is the 98th percentile of |DoD|, rounded up to one significant digit
# %end

import atexit
import io
import math

import grass.script as gs
from grass.exceptions import CalledModuleError
from grass.tools import Tools

TMP_RASTERS = []

# Fraction of a cell below which differences in resolution or grid origin are
# treated as floating point noise rather than misalignment (0.1 mm at 1 m).
GRID_MATCH_TOLERANCE = 1e-4

# The r.dem manual DoD palette as fractions of the saturation value: erosion
# runs yellow to red to magenta, near zero is pale green, deposition runs cyan
# to blue to navy.
PALETTE = [
    (-1.0, "255:0:255"),
    (-0.6, "255:0:0"),
    (-0.3, "255:127:0"),
    (-0.1, "255:255:0"),
    (0.0, "200:255:200"),
    (0.1, "0:255:255"),
    (0.3, "0:191:191"),
    (0.6, "0:0:255"),
    (1.0, "0:0:128"),
]
NULL_COLOR = "240:240:240"


def cleanup():
    if TMP_RASTERS:
        gs.run_command(
            "g.remove",
            type="raster",
            name=",".join(TMP_RASTERS),
            flags="f",
            quiet=True,
            errors="ignore",
        )


def grid_offset(edge, region_edge, res):
    """Offset of a raster edge from the region grid, wrapped to [-res/2, res/2)."""
    off = math.fmod(edge - region_edge, res)
    if off >= res / 2:
        off -= res
    elif off < -res / 2:
        off += res
    return off


def align_input(tools, name, region, interp, tag):
    """Return a raster name on the region grid, resampling when needed."""
    info = gs.raster_info(name)
    ewres, nsres = region["ewres"], region["nsres"]
    dx = grid_offset(info["west"], region["w"], ewres)
    dy = grid_offset(info["north"], region["n"], nsres)
    same_res = (
        abs(info["ewres"] - ewres) <= GRID_MATCH_TOLERANCE * ewres
        and abs(info["nsres"] - nsres) <= GRID_MATCH_TOLERANCE * nsres
    )
    on_grid = (
        abs(dx) <= GRID_MATCH_TOLERANCE * ewres
        and abs(dy) <= GRID_MATCH_TOLERANCE * nsres
    )
    if same_res and on_grid:
        return name

    min_ewres = ewres * (1 - GRID_MATCH_TOLERANCE)
    min_nsres = nsres * (1 - GRID_MATCH_TOLERANCE)
    if info["ewres"] < min_ewres or info["nsres"] < min_nsres:
        gs.warning(
            _(
                "Raster map <{}> is finer than the computational region. "
                "Interpolation samples it without aggregating; consider "
                "r.resamp.stats method=average first."
            ).format(name)
        )
    gs.warning(
        _(
            "Raster map <{name}> is not aligned with the computational region "
            "(resolution {ew:g} x {ns:g}, origin offset {dx:.3f}, {dy:.3f}). "
            "Resampling with {interp} interpolation."
        ).format(
            name=name,
            ew=info["ewres"],
            ns=info["nsres"],
            dx=dx,
            dy=dy,
            interp=interp,
        )
    )
    tmp = gs.append_node_pid(f"tmp_r_dem_dod_{tag}")
    TMP_RASTERS.append(tmp)
    tools.r_resamp_interp(input=name, output=tmp, method=interp, overwrite=True)
    return tmp


def nice_ceil(value):
    """Round a positive value up to one significant digit."""
    magnitude = 10 ** math.floor(math.log10(value))
    return math.ceil(value / magnitude - 1e-9) * magnitude


def saturation(tools, dod):
    """Default palette saturation: 98th percentile of |DoD|."""
    tmp = gs.append_node_pid("tmp_r_dem_dod_abs")
    TMP_RASTERS.append(tmp)
    tools.r_mapcalc(expression=f"{tmp} = abs({dod})", overwrite=True)
    text = tools.r_quantile(input=tmp, percentiles=98).text
    value = float(text.strip().splitlines()[-1].split(":")[-1])
    if not value > 0:
        return 1.0
    return nice_ceil(value)


def color_rules(sat, dmin, dmax):
    """Palette scaled to sat, with end colors extended to the data range."""
    lines = []
    if dmin < -sat:
        lines.append(f"{dmin} {PALETTE[0][1]}")
    lines += [f"{frac * sat:g} {rgb}" for frac, rgb in PALETTE]
    if dmax > sat:
        lines.append(f"{dmax} {PALETTE[-1][1]}")
    lines.append(f"nv {NULL_COLOR}")
    return "\n".join(lines) + "\n"


def raster_units(name):
    """Units metadata of a raster, or an empty string when unset."""
    units = (gs.raster_info(name).get("units") or "").strip().strip('"')
    return "" if units.lower() == "none" else units


def read_timestamp(tools, name):
    """Return (start, end) strings of a raster timestamp, or None."""
    try:
        text = tools.r_timestamp(map=name).text.strip()
    except CalledModuleError:
        return None
    if not text or text == "none":
        return None
    parts = [p.strip() for p in text.split("/")]
    return parts[0], parts[-1]


def main():
    options, flags = gs.parser()
    dem = options["dem"]
    reference = options["reference"]
    output = options["output"]
    interp = options["interp"]
    user_range = options["range"]

    if user_range and float(user_range) <= 0:
        gs.fatal(_("Option <range> must be greater than zero."))

    tools = Tools()
    region = gs.region()
    later = align_input(tools, dem, region, interp, "dem")
    earlier = align_input(tools, reference, region, interp, "ref")

    tools.r_mapcalc(
        expression=f"{output} = double({later}) - double({earlier})",
        overwrite=gs.overwrite(),
    )

    stats = gs.raster_info(output)
    if stats["min"] is None or stats["max"] is None:
        gs.fatal(_("DEM of Difference <{}> has no valid cells.").format(output))
    sat = float(user_range) if user_range else saturation(tools, output)
    tools.r_colors(
        map=output, rules=io.StringIO(color_rules(sat, stats["min"], stats["max"]))
    )

    dem_units = raster_units(dem)
    ref_units = raster_units(reference)
    if dem_units and ref_units and dem_units != ref_units:
        gs.warning(
            _("Input units differ: <{}> is '{}', <{}> is '{}'.").format(
                dem, dem_units, reference, ref_units
            )
        )

    gs.raster_history(output, overwrite=True)
    support = {
        "map": output,
        "title": "DEM of Difference",
        "description": f"{dem} - {reference}",
        "source1": dem,
        "source2": reference,
        "history": f"interp={interp}, palette saturation={sat:g}",
    }
    if dem_units:
        support["units"] = dem_units
    tools.r_support(**support)

    later_ts = read_timestamp(tools, dem)
    earlier_ts = read_timestamp(tools, reference)
    if later_ts and earlier_ts:
        interval = f"{earlier_ts[0]} / {later_ts[1]}"
        try:
            tools.r_timestamp(map=output, date=interval)
        except CalledModuleError:
            gs.warning(
                _("Could not set timestamp '{}' on <{}>.").format(interval, output)
            )


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
