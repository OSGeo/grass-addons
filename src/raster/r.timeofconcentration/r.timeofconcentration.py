#!/usr/bin/env python

##############################################################################
# MODULE:    r.timeofconcentration
#
# AUTHOR(S): Abdullah Azzam <mabdazzam@outlook.com>
#
# PURPOSE:   generates a time of concentration raster using upstream flow length and
#            average slope
#
# K: (C) 2025 by Abdullah Azzam and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""Generates a time of concentration raster using upstream flow length and slope"""

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

# %option G_OPT_R_OUTPUT
# % key: time_concentration
# % description: Name for output time of concentration raster map [hours]
# % required: yes
# % guisection: outputs
# %end

# %option G_OPT_R_INPUT
# % key: streams
# % description: Name of optional input stream raster map consistent with 'direction'; if not provided, a stream raster is derived using r.watershed
# % required: no
# % guisection: inputs
# %end

# %option
# % key: threshold
# % type: integer
# % description: Threshold (number of cells) used to derive streams when 'streams' is not provided (lower value = denser network)
# % required: no
# % guisection: inputs
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
            name=_TMP_RAST,  # list created above
            flags="f",
            quiet=True,
            errors="ignore",  # don't complain if something is already gone
        )


def tmp_rast(basename: str) -> str:
    """Return a unique, style-compliant temp raster name and register it for cleanup."""
    # recommended: all temps begin with 'TMP_' + module tag
    name = gs.append_node_pid(basename)
    _TMP_RAST.append(name)
    return name


def main():
    options, flags = gs.parser()

    # required
    elev = options["elevation"]
    fdr = options["direction"]
    out = options["time_concentration"]

    # optional inputs
    streams_opt = options.get("streams")
    threshold = int(options.get("threshold")) if options.get("threshold") else 1
    outlets = options.get("outlets")

    # kirpich parameters fixed for meters (α,β as a,b)
    a = 0.77
    b = -0.385
    K = 0.01947

    # numeric floors to avoid blowup
    slope_min = float(options["slope_min"]) if options.get("slope_min") else 1e-4
    length_min = float(options["length_min"]) if options.get("length_min") else 10.0

    # optional diagnostics to promote temps
    out_L = options.get("length")
    out_DZ = options.get("drop")
    out_Savg = options.get("sbar")

    # basic checks
    gs.message(_("Checking inputs..."))
    res = gs.find_file(elev, element="raster")
    if not res["file"]:
        gs.fatal(_("Raster map <{name}> not found").format(name=elev))

    res = gs.find_file(fdr, element="raster")
    if not res["file"]:
        gs.fatal(_("Raster map <{name}> not found").format(name=fdr))

    # optional: validate only if provided
    if streams_opt:
        res = gs.find_file(streams_opt, element="raster")
        if not res["file"]:
            gs.fatal(
                _("Optional 'streams' raster <{name}> not found").format(
                    name=streams_opt
                )
            )

    if outlets:
        res = gs.find_file(outlets, element="raster")
        if not res["file"]:
            gs.fatal(
                _("Optional 'outlets' raster <{name}> not found").format(name=outlets)
            )

    # temps; write directly to user outputs when provided
    L = out_L if out_L else tmp_rast("TMP_r_toc_L")
    DZ = tmp_rast("TMP_r_toc_DZ")
    DZp = out_DZ if out_DZ else tmp_rast("TMP_r_toc_DZp")
    Savg = out_Savg if out_Savg else tmp_rast("TMP_r_toc_Savg")

    # streams: provided or derived?
    if streams_opt:
        gs.message(
            _("Using provided streams raster <{name}>...").format(name=streams_opt)
        )
        streams_rast = streams_opt
    else:
        streams_rast = tmp_rast("TMP_r_toc_streams")
        gs.message(
            _("Deriving streams with r.watershed (threshold={thr})...").format(
                thr=threshold
            )
        )
        gs.run_command(
            "r.watershed",
            elevation=elev,
            threshold=threshold,
            stream=streams_rast,
            quiet=True,
        )

    # upstream metrics: L (distance), DZ (drop)
    gs.message(_("Computing upstream distance and drop with r.stream.distance..."))
    gs.run_command(
        "r.stream.distance",
        stream_rast=streams_rast,
        direction=fdr,
        elevation=elev,
        method="upstream",
        distance=L,
        difference=DZ,
        quiet=True,
    )

    outlets_expr = outlets if outlets else "1"
    # slope and tc
    if out_DZ or out_Savg:
        gs.message(_("Computing diagnostics: drop and path-average slope..."))
        # compute separately for diagnostics
        gs.mapcalc(f"{DZp} = max({DZ}, 0)", quiet=True)
        gs.mapcalc(f"{Savg} = if ({L} > 0, max({DZp}/{L}, {slope_min}), 0)", quiet=True)
        Savg_expr = Savg
    else:
        # faster all at once
        gs.message(_("Computing slope inline without diagnostics..."))
        Savg_expr = f"if ({L} > 0, max(max({DZ}, 0)/{L}, {slope_min}), 0)"

    gs.message(
        _("Computing time of concentration to raster <{out}>...").format(out=out)
    )
    gs.mapcalc(
        f"{out} = if(!isnull({outlets_expr}) && {L} >= {length_min}, "
        f"{K} * pow({L},{a}) * pow({Savg_expr},{b}) / 60.0, null())",
        quiet=True,
    )

    gs.raster_history(out)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())
