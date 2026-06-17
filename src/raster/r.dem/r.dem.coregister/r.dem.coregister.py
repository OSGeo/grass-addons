#!/usr/bin/env python3
# pyright: reportMissingImports=false

##############################################################################
# MODULE:    r.dem.coregister
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Co-register post-event DSM to reference DEM using road PGCPs
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

# %module
# % description: Co-register post-event DSM to reference DEM using road PGCPs
# % keyword: raster
# % keyword: terrain
# % keyword: coregistration
# % keyword: DEM
# % keyword: photogrammetry
# % keyword: disaster response
# %end

# %option G_OPT_R_INPUT
# % key: dem
# % description: Post-event DSM to co-register
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % key: reference
# % description: Reference DEM (e.g., pre-event LiDAR DTM/DSM)
# % required: yes
# %end

# %option G_OPT_V_INPUT
# % key: roads
# % description: Road centerlines vector for PGCP extraction
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Co-registered DSM output name
# % required: yes
# %end

# %option
# % key: method
# % type: string
# % description: Co-registration method
# % options: pgcp_vertical,nk,nk_icp
# % answer: pgcp_vertical
# % required: no
# %end

# %option
# % key: buffer
# % type: double
# % description: Buffer distance (m) around road centerlines for PGCP sampling
# % answer: 2.0
# % required: no
# %end

# %option
# % key: min_points
# % type: integer
# % description: Minimum number of PGCPs required to proceed
# % answer: 30
# % required: no
# %end

# %option G_OPT_F_OUTPUT
# % key: bias_output
# % description: CSV file path for per-PGCP residual statistics
# % required: no
# %end

# %flag
# % key: v
# % description: Verbose — write per-PGCP residuals to bias_output CSV
# %end

import sys
import os
import csv
import numpy as np

import gettext
import grass.script as gs

# Set up translation function
_ = gettext.gettext


def pgcp_vertical_correction(
    dem, reference, roads, output, buffer, min_points, bias_output, verbose
):
    """
    Extract elevation residuals from stable road pixels, compute robust
    median vertical bias, and apply correction via r.mapcalc.

    Returns: dict of bias statistics
    """
    tmp_prefix = f"tmp_rdemcoreg_{os.getpid()}"
    buf_v = f"{tmp_prefix}_buf"
    buf_r = f"{tmp_prefix}_bufr"
    diff_r = f"{tmp_prefix}_diff"

    # Buffer road centerlines
    gs.run_command(
        "v.buffer",
        input=roads,
        output=buf_v,
        distance=buffer,
        overwrite=True,
        quiet=True,
    )
    gs.run_command(
        "v.to.rast",
        input=buf_v,
        output=buf_r,
        use="val",
        value=1,
        overwrite=True,
        quiet=True,
    )

    # Difference DSM - Reference within road buffer
    gs.mapcalc(
        f"{diff_r} = if({buf_r} == 1, {dem} - {reference}, null())",
        overwrite=True,
        quiet=True,
    )

    # Read residuals
    raw = gs.read_command("r.stats", input=diff_r, flags="1n", separator=",").strip()
    if not raw:
        gs.fatal(_("No PGCP samples extracted. Check road vector and region."))

    residuals = np.array([float(v) for v in raw.split("\n") if v.strip()])

    if len(residuals) < int(min_points):
        gs.warning(
            _(
                "Only {len_residuals} PGCP samples found "
                "(minimum {min_points}). Proceeding with caution."
            )
            % {"len_residuals": len(residuals), "min_points": min_points}
        )

    # Robust statistics
    median_bias = float(np.median(residuals))
    nmad = float(1.4826 * np.median(np.abs(residuals - median_bias)))
    rmse = float(np.sqrt(np.mean(residuals**2)))
    n = len(residuals)

    gs.message(_("PGCP vertical correction:"))
    gs.message(f"  N samples:   {n}")
    gs.message(f"  Median bias: {median_bias:.4f} m")
    gs.message(f"  NMAD:        {nmad:.4f} m")
    gs.message(f"  RMSE:        {rmse:.4f} m")

    # Apply correction
    gs.mapcalc(f"{output} = {dem} - {median_bias}", overwrite=True)
    gs.run_command(
        "r.support",
        map=output,
        title=f"Co-registered DSM (bias={median_bias:.4f}m removed)",
        description=f"r.dem.coregister: PGCP vertical, N={n}, "
        f"NMAD={nmad:.4f}m, RMSE={rmse:.4f}m",
    )

    # Optional CSV output
    if verbose and bias_output:
        # Get per-cell x,y,z for CSV
        xyz_raw = gs.read_command(
            "r.stats", input=f"{diff_r}", flags="1gn", separator=","
        ).strip()
        rows = [r.split(",") for r in xyz_raw.split("\n") if r.strip()]
        with open(bias_output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y", "residual_m"])
            writer.writerows(rows)
        gs.message(f"PGCP residuals written to: {bias_output}")

    # Cleanup temp maps
    gs.run_command(
        "g.remove",
        type="raster,vector",
        name=f"{tmp_prefix}_buf,{tmp_prefix}_bufr,{tmp_prefix}_diff",
        flags="f",
        quiet=True,
    )

    return {"n": n, "median_bias": median_bias, "nmad": nmad, "rmse": rmse}


def main():
    dem = options["dem"]
    reference = options["reference"]
    roads = options["roads"]
    output = options["output"]
    method = options["method"]
    buffer = float(options["buffer"])
    min_points = int(options["min_points"])
    bias_out = options.get("bias_output", "")
    verbose = flags["v"]

    # PGCP vertical correction (always runs first)
    tmp_pgcp = f"tmp_rdemcoreg_pgcp_{os.getpid()}"
    pgcp_vertical_correction(
        dem=dem,
        reference=reference,
        roads=roads,
        output=tmp_pgcp if method != "pgcp_vertical" else output,
        buffer=buffer,
        min_points=min_points,
        bias_output=bias_out,
        verbose=verbose,
    )

    if method == "pgcp_vertical":
        gs.message("Method: pgcp_vertical — done.")
        return

    # N&K horizontal + vertical refinement
    if method in ("nk", "nk_icp"):
        nk_out = f"tmp_rdemcoreg_nk_{os.getpid()}" if method == "nk_icp" else output
        gs.run_command(
            "r.dem.nk",
            dem=nk_out if method == "nk" else tmp_pgcp,
            reference=reference,
            output=nk_out,
            overwrite=True,
        )
        if method == "nk":
            return

    # Stage 3: ICP refinement
    if method == "nk_icp":
        gs.run_command(
            "r.dem.icp",
            dem=f"tmp_rdemcoreg_nk_{os.getpid()}",
            reference=reference,
            output=output,
            overwrite=True,
        )

    # Cleanup intermediates
    for tmp in [tmp_pgcp, f"tmp_rdemcoreg_nk_{os.getpid()}"]:
        if gs.find_file(tmp, element="raster")["name"]:
            gs.run_command("g.remove", type="raster", name=tmp, flags="f", quiet=True)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
