#!/usr/bin/env python

##############################################################################
# MODULE:    r.timeofconcentration
#
# AUTHOR(S): Abdullah Azzam <mabdazzam@outlook.com>
#
# PURPOSE:   generates a time of concentration raster using the Kirpich
#            Equation
#
# K: (C) 2025 by Abdullah Azzam and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""Generates a time of concentration raster using the Kirpich Equation"""

# %module
# % description: Computes per-cell time of concentration (Tc) using the Kirpich equation from longest upstream flow-path length and path-average slope.
# % keyword: raster
# % keyword: hydrology
# % keyword: time of concentration
# % keyword: SCS
# %end

# %option G_OPT_R_ELEV
# % key: elevation
# % description: Name of input elevation raster map [m]
# % required: yes
# % guisection: inputs
# %end

# %option G_OPT_R_INPUT
# % key: direction
# % description: Name of input flow direction raster map (from r.watershed or r.stream.extract)
# % required: yes
# % guisection: inputs
# %end

# %option G_OPT_R_INPUT
# % key: streams
# % description: Name of input stream raster map consistent with 'direction' (from r.watershed or r.stream.extract)
# % required: yes
# % guisection: inputs
# %end

# %option G_OPT_R_OUTPUT
# % key: time_concentration
# % description: Name for output time of concentration raster map [hours]
# % required: yes
# % guisection: outputs
# %end

# %option G_OPT_R_INPUT
# % key: outlets
# % description: Name of optional input outlets raster map; when set, Tc is reported only at these cells
# % required: no
# % guisection: scope
# %end

# %option
# % key: slope_min
# % type: double
# % answer: 1e-4
# % description: Minimum path-average slope (unitless) to avoid division by zero on flats
# % required: no
# % guisection: thresholds
# %end

# %option
# % key: length_min
# % type: double
# % answer: 10
# % description: Minimum upstream flow-path length to report Tc [m]
# % required: no
# % guisection: thresholds
# %end

# %option
# % key: vertical_units
# % type: string
# % options: meters,feet,factor
# % answer: meters
# % description: Vertical units of elevation raster (converted to meters internally)
# % required: no
# % guisection: vertical
# %end

# %option
# % key: factor
# % type: double
# % description: Conversion factor to meters when vertical_units=factor (ensure factor * units = meters)
# % required: no
# % guisection: vertical
# %end

# %option G_OPT_R_OUTPUT
# % key: length
# % description: Name for optional output longest upstream flow-path length raster map L [m]
# % required: no
# % guisection: diagnostics
# %end

# %option G_OPT_R_OUTPUT
# % key: drop
# % description: Name for optional output flow-path elevation drop raster map delta_z (>= 0) [m]
# % required: no
# % guisection: diagnostics
# %end

# %option G_OPT_R_OUTPUT
# % key: sbar
# % description: Name for optional output path-average slope raster map S_bar = max(delta_z / L, slope_min) [unitless]
# % required: no
# % guisection: diagnostics
# %end

import sys
import atexit
import grass.script as gs
from grass.script import parser, run_command, fatal, warning

_TMP_RAST = []  # temp rasters; removed on exit


def cleanup():
    """Remove all temp rasters created by this script."""
    if _TMP_RAST:
        gs.run_command(
            "g.remove",
            type="raster",
            name=",".join(_TMP_RAST),
            flags="f",
            quiet=True,
            errors="ignore",
        )


def tmp_rast(basename: str) -> str:
    """Return a unique temp raster name and register it for cleanup."""
    name = gs.append_node_pid(basename)
    _TMP_RAST.append(name)
    return name


def main():
    options, flags = gs.parser()

    # required
    elevation = options["elevation"]
    direction = options["direction"]
    streams = options["streams"]
    time_concentration = options["time_concentration"]

    # optional
    outlets = options.get("outlets")

    slope_min = float(options["slope_min"]) if options.get("slope_min") else 1e-4
    length_min = float(options["length_min"]) if options.get("length_min") else 10.0

    vertical_units = options.get("vertical_units") or "meters"
    if vertical_units in ("meters", "feet"):
        if options["factor"]:
            gs.fatal(_("Factor must be used only when vertical_units=factor"))
        factor = 1 if vertical_units == "meters" else 1.0 / 3.28084
    elif options["factor"]:
        factor = float(options.get("factor"))
    else:
        gs.fatal(_("Factor must be provided when vertical_units=factor"))

    length = options.get("length")
    drop = options.get("drop")
    sbar = options.get("sbar")

    # kirpich parameters (metric; α,β as a,b)
    a = 0.77
    b = -0.385
    K = 0.01947

    gs.message(_("Checking inputs..."))

    if not gs.find_file(elevation, element="raster")["file"]:
        gs.fatal(_("raster map <{name}> not found").format(name=elevation))

    if not gs.find_file(direction, element="raster")["file"]:
        gs.fatal(_("raster map <{name}> not found").format(name=direction))

    if not gs.find_file(streams, element="raster")["file"]:
        gs.fatal(_("stream raster <{name}> not found").format(name=streams))

    if outlets:
        if not gs.find_file(outlets, element="raster")["file"]:
            gs.fatal(
                _("optional 'outlets' raster <{name}> not found").format(name=outlets)
            )

    # temps / targets
    L = length if length else tmp_rast("TMP_r_toc_L")
    DZ = tmp_rast("TMP_r_toc_DZ")
    DZ_m = tmp_rast("TMP_r_toc_DZ_m")
    DZp = drop if drop else tmp_rast("TMP_r_toc_DZp")
    Savg = sbar if sbar else tmp_rast("TMP_r_toc_Savg")

    gs.message(
        _("Computing upstream distance and elevation drop with r.stream.distance...")
    )
    gs.run_command(
        "r.stream.distance",
        stream_rast=streams,
        direction=direction,
        elevation=elevation,
        method="upstream",
        distance=L,
        difference=DZ,
        quiet=True,
    )

    # convert vertical to meters if needed
    if factor != 1.0:
        gs.message(
            _("converting elevation drops to meters (factor = {f})...").format(
                f=f"{factor:.5f}"
            )
        )
        gs.mapcalc(f"{DZ_m} = {DZ} * {factor}", quiet=True)
        dz_src = DZ_m
    else:
        dz_src = DZ

    outlets_expr = outlets if outlets else "1"

    # diagnostics or inline slope
    if drop or sbar:
        gs.message(_("Computing diagnostics: drop and path-average slope..."))
        gs.mapcalc(f"{DZp} = max({dz_src}, 0)", quiet=True)
        gs.mapcalc(
            f"{Savg} = if ({L} > 0, max({DZp}/{L}, {slope_min}), 0)",
            quiet=True,
        )
        savg_expr = Savg
    else:
        # gs.message(_("Computing slope inline without diagnostics..."))
        savg_expr = f"if ({L} > 0, max(max({dz_src}, 0)/{L}, {slope_min}), 0)"

    gs.message(
        _("Computing time of concentration to raster <{out}>...").format(
            out=time_concentration
        )
    )
    gs.mapcalc(
        f"{time_concentration} = if(!isnull({outlets_expr}) && {L} >= {length_min}, "
        f"{K} * pow({L},{a}) * pow({savg_expr},{b}) / 60.0, null())",
        quiet=True,
    )

    gs.raster_history(time_concentration)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())
