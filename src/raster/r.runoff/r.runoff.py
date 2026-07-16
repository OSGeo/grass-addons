#!/usr/bin/env python

##############################################################################
# MODULE:    r.runoff
#
# AUTHOR(S): Abdullah Azzam <mabdazzam@outlook.com>
#
# PURPOSE:   Computes the runoff depth, volume, and peak discharge rasters using the SCS Curve Number Method
#
# SPDX-FileCopyrightText: 2025 Abdullah Azzam
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

"""Computes the runoff depth, volume, and peak discharge rasters using the SCS Curve Number Method"""


# %module
# % description: Computes runoff depth, volume and peak discharge for each cell using SCS Curve Number method.
# % keyword: hydrology
# % keyword: runoff
# % keyword: SCS
# % keyword: curve number
# %end

# %option G_OPT_R_INPUT
# % key: rainfall
# % description: Name of input rainfall depth raster map [mm] (event total)
# % required: yes
# % guisection: inputs
# %end

# %option
# % key: duration
# % type: double
# % description: Storm duration D [hours] (used for time_to_peak and peak_discharge)
# % required: no
# % options: 0-
# % guisection: upstream
# %end

# %option G_OPT_R_INPUT
# % key: curve_number
# % description: Name of input Curve Number raster map (0 < CN <= 100)
# % required: yes
# % guisection: inputs
# %end

# %option G_OPT_R_INPUT
# % key: direction
# % description: Name of input flow direction raster map (for r.accumulate / r.watershed)
# % required: no
# % guisection: upstream
# %end

# %option
# % key: lambda
# % type: double
# % description: Initial abstraction ratio lambda (0 <= lambda <= 0.6)
# % answer: 0.2
# % required: no
# % options: 0-0.6
# % guisection: parameters
# %end

# %option G_OPT_R_INPUT
# % key: time_concentration
# % description: Name of input time of concentration raster map [hours]
# % required: no
# % guisection: upstream
# %end

# %option G_OPT_R_OUTPUT
# % key: runoff_depth
# % description: Name for output runoff depth raster map [mm]
# % required: yes
# % guisection: outputs
# %end

# %option G_OPT_R_OUTPUT
# % key: runoff_volume
# % description: Name for output per-cell runoff volume raster map [m3]
# % required: no
# % guisection: outputs
# %end

# %option G_OPT_R_OUTPUT
# % key: upstream_area
# % description: Name for optional output upstream drainage area raster map [km2]
# % required: no
# % guisection: upstream
# %end

# %option G_OPT_R_OUTPUT
# % key: upstream_runoff_depth
# % description: Name for optional output upstream area weighted average runoff depth raster map [mm]
# % required: no
# % guisection: upstream
# %end

# %option G_OPT_R_OUTPUT
# % key: upstream_runoff_volume
# % description: Name for optional output upstream runoff volume raster map [m3]
# % required: no
# % guisection: upstream
# %end

# %option G_OPT_R_OUTPUT
# % key: time_to_peak
# % description: Name for optional output time to peak raster map [hours]
# % required: no
# % guisection: upstream
# %end

# %option G_OPT_R_OUTPUT
# % key: peak_discharge
# % description: Name for optional output peak discharge raster map [m3/s]
# % required: no
# % guisection: upstream
# %end

import os
import sys
import atexit
import grass.script as gs


# temp handling: one atexit per temp
def remove(name):
    gs.run_command(
        "g.remove",
        type="raster",
        name=name,
        flags="f",
        quiet=True,
        errors="ignore",
    )


def mktemp(prefix: str) -> str:
    """create a unique temp map name and register its cleanup once"""
    name = gs.append_node_pid(f"tmp_r_runoff_{prefix}")
    atexit.register(remove, name)
    return name


def require_raster(name: str, label: str):
    if not name or not gs.find_file(name, element="cell")["name"]:
        gs.fatal(_("Raster map <{name}> not found").format(name=name))


def want_upstream(opts: dict) -> bool:
    return any(
        opts.get(k)
        for k in (
            "upstream_area",
            "upstream_runoff_depth",
            "upstream_runoff_volume",
            "time_to_peak",
            "peak_discharge",
        )
    )


def main():
    options, flags = gs.parser()

    # required
    rainfall = options["rainfall"]
    cn = options["curve_number"]
    qout = options["runoff_depth"]
    vout = options["runoff_volume"]  # optional
    lambda_ratio = float(options["lambda"])

    require_raster(rainfall, "rainfall")
    require_raster(cn, "curve_number")

    # upstream bundle
    do_up = want_upstream(options)
    flow_dir = options.get("direction")
    time_conc = options.get("time_concentration")
    duration_hours = options.get("duration")
    upstream_area_out = options.get("upstream_area")
    upstream_runoff_depth_out = options.get("upstream_runoff_depth")
    upstream_runoff_volume_out = options.get("upstream_runoff_volume")
    ttp_out = options.get("time_to_peak")
    peak_out = options.get("peak_discharge")

    if do_up:
        if not (flow_dir and time_conc and duration_hours):
            gs.fatal(
                _(
                    "Options direction=, time_concentration=, and duration= are required for upstream outputs"
                )
            )
        require_raster(flow_dir, "direction")
        require_raster(time_conc, "time_concentration")
        duration_hours = float(duration_hours)
        if duration_hours <= 0.0:
            gs.fatal(_("duration must be > 0 [hours]"))

    # S (storage) [mm] and Q (runoff depth) [m]
    S = mktemp("S_mm")
    gs.mapcalc(f"{S} = if(isnull({cn}), null(), 25400.0/{cn} - 254.0)", quiet=True)

    gs.message(_("Computing runoff depth [mm]"))
    gs.mapcalc(
        f"{qout} = if(isnull({rainfall}) || isnull({S}), null(), "
        f"if({rainfall} > {lambda_ratio}*{S}, "
        f"(({rainfall} - {lambda_ratio}*{S})^2) / ({rainfall} + (1.0 - {lambda_ratio})*{S}), "
        f"0.0))",
        quiet=True,
    )

    # per-cell volume [m3]
    area_m2 = mktemp("area_m2")
    q_m = mktemp("q_m")
    v_m3 = vout if vout else mktemp("v_m3")

    gs.mapcalc(f"{area_m2} = area()", quiet=True)
    gs.message(_("Computing per-cell volume [m³]"))
    gs.mapcalc(f"{q_m} = {qout} / 1000.0", quiet=True)
    gs.mapcalc(f"{v_m3} = {q_m} * {area_m2}", quiet=True)

    # totals & quick stats (using -g for 8.4 compatibility; printing stderr just for info)
    vst = gs.parse_command("r.univar", map=v_m3, flags="g", quiet=True)
    total = float(vst.get("sum", 0.0)) if vst else 0.0
    gs.message(_("Total runoff volume: {total:.2f} m³").format(total=total))

    qst = gs.parse_command("r.univar", map=qout, flags="g", quiet=True)
    qmax = float(qst.get("max", 0.0)) if qst else 0.0
    gs.message(_("Maximum runoff depth: {qmax:.2f} mm").format(qmax=qmax))

    # upstream accumulations & peak
    if do_up:
        gs.message(_("Computing upstream area [km²] and volume [m³]"))

        w_km2 = mktemp("w_km2")
        gs.mapcalc(f"{w_km2} = {area_m2} / 1000000.0", quiet=True)

        a_up = upstream_area_out if upstream_area_out else mktemp("upstream_area_km2")
        v_up = (
            upstream_runoff_volume_out
            if upstream_runoff_volume_out
            else mktemp("upstream_runoff_volume_m3")
        )

        gs.run_command(
            "r.accumulate",
            direction=flow_dir,
            format="auto",
            weight=w_km2,
            accumulation=a_up,
            accumulation_type="DCELL",
            quiet=True,
        )
        gs.run_command(
            "r.accumulate",
            direction=flow_dir,
            format="auto",
            weight=v_m3,
            accumulation=v_up,
            accumulation_type="DCELL",
            quiet=True,
        )

        # upstream-average runoff depth [mm] = m3 / (km2 * 1000)
        qavg = (
            upstream_runoff_depth_out
            if upstream_runoff_depth_out
            else mktemp("upstream_runoff_depth_mm")
        )
        gs.message(_("Computing upstream-average runoff depth [mm]"))
        gs.mapcalc(
            f"{qavg} = if({a_up} > 0.0, {v_up} / ({a_up} * 1000.0), 0.0)", quiet=True
        )

        # time to peak [hours] = 0.5*D + 0.6*Tc
        tp = ttp_out if ttp_out else mktemp("tp_h")
        gs.message(_("Computing time to peak [hours]"))
        gs.mapcalc(
            f"{tp} = if(isnull({time_conc}), null(), 0.5*{duration_hours} + 0.6*{time_conc})",
            quiet=True,
        )

        # peak discharge [m3/s] = 0.208 * A[km2] * Q[mm] / tp[h]
        if peak_out:
            gs.message(_("Computing peak discharge [m³/s]"))
            gs.mapcalc(
                f"{peak_out} = if(isnull({tp}) || {tp} <= 0.0, 0.0, 0.208 * {a_up} * {qavg} / {tp})",
                quiet=True,
            )
            pst = gs.parse_command("r.univar", map=peak_out, flags="g", quiet=True)
            pmax = float(pst.get("max", 0.0)) if pst else 0.0
            gs.message(_("Peak discharge (max): {pmax:.3f} m³/s").format(pmax=pmax))

    return 0


if __name__ == "__main__":
    sys.exit(main())
