#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.coregister
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Co-register post-event DSM to reference DEM using PGCPs
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Co-register post-event DSM to reference DEM using PGCPs
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
# % key: pgcp
# % label: Pseudo ground control points (PGCPs) (e.g. roads, buildings, fire hydrants) vector for PGCP extraction
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
# % options: pgcp_vertical,nk,nk_icp,icp
# % answer: pgcp_vertical
# % required: no
# %end

# %option
# % key: buffer
# % type: double
# % description: Buffer distance (m) around PGCP features for residual sampling
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

# %option G_OPT_R_INPUT
# % key: stable_mask
# % description: Stable-terrain mask (1=stable); required by method nk and nk_icp
# % required: no
# %end

# %option G_OPT_F_OUTPUT
# % key: bias_output
# % description: CSV file path for per-PGCP residual statistics
# % required: no
# %end

# %option G_OPT_F_OUTPUT
# % key: transform_output
# % description: Write the solved transform (PGCP, N&K, ICP components) to a file
# % required: no
# %end

# %option G_OPT_F_INPUT
# % key: apply_transform
# % description: Replay a saved transform onto dem (shared horizontal, per-surface vertical) instead of solving
# % required: no
# %end

# %flag
# % key: v
# % description: Verbose: write per-PGCP residuals to bias_output CSV
# %end

import atexit
import sys
import os
import csv
import math
import numpy as np

import grass.script as gs

TMP_RASTERS = []
TMP_VECTORS = []


def cleanup():
    if TMP_RASTERS:
        gs.run_command(
            "g.remove",
            type="raster",
            name=",".join(TMP_RASTERS),
            flags="f",
            quiet=True,
        )
    if TMP_VECTORS:
        gs.run_command(
            "g.remove",
            type="vector",
            name=",".join(TMP_VECTORS),
            flags="f",
            quiet=True,
        )


def read_keyval(path):
    """Parse a `key=value` transform file into a dict of strings."""
    data = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def write_combined_transform(path, method, pgcp_dz, nk, icp):
    """Write the composed PGCP + N&K + ICP transform to a file."""
    with open(path, "w") as f:
        f.write("# r.dem.coregister transform\n")
        f.write(f"method={method}\n")
        f.write(f"pgcp_dz={pgcp_dz:.10f}\n")
        f.write(f"nk_dz={nk['dz']:.10f}\n")
        f.write(f"nk_dx={nk['dx']:.10f}\n")
        f.write(f"nk_dy={nk['dy']:.10f}\n")
        f.write(f"icp_tx={icp['tx']:.10f}\n")
        f.write(f"icp_ty={icp['ty']:.10f}\n")
        f.write(f"icp_tz={icp['tz']:.10f}\n")
        f.write(f"icp_yaw={icp['yaw']:.10f}\n")
    gs.message(_("Transform written to: {}").format(path))


def pgcp_vertical_correction(
    dem, reference, pgcp, output, buffer, min_points, bias_output, verbose
):
    """
    Extract elevation residuals from stable PGCP pixels, compute robust
    median vertical bias, and apply correction via r.mapcalc.

    Returns: dict of bias statistics
    """
    tmp_prefix = f"tmp_rdemcoreg_{os.getpid()}"
    buf_v = f"{tmp_prefix}_buf"
    buf_r = f"{tmp_prefix}_bufr"
    diff_r = f"{tmp_prefix}_diff"
    TMP_VECTORS.append(buf_v)
    TMP_RASTERS.extend([buf_r, diff_r])

    # Buffer the PGCP features
    gs.run_command(
        "v.buffer",
        input=pgcp,
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

    # Difference DSM - Reference within PGCP buffer
    gs.mapcalc(
        f"{diff_r} = if({buf_r} == 1, {dem} - {reference}, null())",
        overwrite=True,
        quiet=True,
    )

    # Read residuals
    raw = gs.read_command("r.stats", input=diff_r, flags="1n", separator=",").strip()
    if not raw:
        gs.fatal(_("No PGCP samples extracted. Check PGCP vector and region."))

    residuals = np.array([float(v) for v in raw.split("\n") if v.strip()])

    if len(residuals) < int(min_points):
        gs.warning(
            _(
                "Only {n} PGCP samples found (minimum {min}). Proceeding with caution."
            ).format(n=len(residuals), min=min_points)
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
    gs.mapcalc(f"{output} = {dem} - {median_bias}", overwrite=gs.overwrite())
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

    return {"n": n, "median_bias": median_bias, "nmad": nmad, "rmse": rmse}


def apply_saved_transform(
    dem, reference, pgcp, output, xform_path, buffer, min_points, bias_out, verbose
):
    """Replay a saved transform onto a new surface.

    The horizontal alignment (N&K dx, dy and ICP dx, dy, yaw) is shared across
    surfaces from the same acquisition, but the vertical bias is re-estimated
    per surface via the PGCP step, since the DSM and DTM offsets differ.
    """
    t = read_keyval(xform_path)
    method = t.get("method", "nk_icp")
    nk_dx = float(t.get("nk_dx", 0.0))
    nk_dy = float(t.get("nk_dy", 0.0))
    icp_tx = float(t.get("icp_tx", 0.0))
    icp_ty = float(t.get("icp_ty", 0.0))
    icp_yaw_rad = float(t.get("icp_yaw", 0.0))

    pid = os.getpid()
    full_mask = f"tmp_rdemcoreg_amask_{pid}"
    tmp_h = f"tmp_rdemcoreg_h_{pid}"
    tmp_hi = f"tmp_rdemcoreg_hi_{pid}"

    # The icp method has no N&K component, so skip r.dem.nk entirely and feed
    # the original DEM straight into the ICP apply step.
    if method == "icp":
        horiz = dem
    else:
        nk_xform = gs.tempfile()
        # r.dem.nk requires a mask; in apply mode it only defines the residual
        # map, so a full-coverage mask is sufficient.
        TMP_RASTERS.extend([full_mask, tmp_h, f"{tmp_h}_resid"])
        gs.mapcalc(
            f"{full_mask} = if(!isnull({dem}), 1, null())", overwrite=True, quiet=True
        )

        # Apply the N&K horizontal shift only (dz = 0; vertical handled by PGCP).
        with open(nk_xform, "w") as f:
            f.write(f"dz=0.0\ndx={nk_dx:.10f}\ndy={nk_dy:.10f}\n")
        gs.run_command(
            "r.dem.nk",
            sfm=dem,
            lidar=reference,
            stable_mask=full_mask,
            output=tmp_h,
            apply_transform=nk_xform,
            overwrite=True,
        )
        horiz = tmp_h

    # Apply the ICP horizontal + yaw (tz = 0); init_yaw is in degrees.
    if method in ("nk_icp", "icp"):
        TMP_RASTERS.append(tmp_hi)
        gs.run_command(
            "r.dem.icp",
            reference=reference,
            source=horiz,
            output=tmp_hi,
            max_iterations=0,
            init_dx=icp_tx,
            init_dy=icp_ty,
            init_dz=0.0,
            init_yaw=math.degrees(icp_yaw_rad),
            overwrite=True,
        )
        horiz = tmp_hi

    # Re-estimate the per-surface vertical bias on the horizontally aligned DEM.
    pgcp_vertical_correction(
        dem=horiz,
        reference=reference,
        pgcp=pgcp,
        output=output,
        buffer=buffer,
        min_points=min_points,
        bias_output=bias_out,
        verbose=verbose,
    )


def main():
    dem = options["dem"]
    reference = options["reference"]
    pgcp = options["pgcp"]
    output = options["output"]
    method = options["method"]
    buffer = float(options["buffer"])
    min_points = int(options["min_points"])
    stable_mask = options["stable_mask"]
    bias_out = options.get("bias_output", "")
    xform_out = options.get("transform_output", "")
    xform_in = options.get("apply_transform", "")
    verbose = flags["v"]

    # Replay mode: apply a transform solved on another surface.
    if xform_in:
        apply_saved_transform(
            dem,
            reference,
            pgcp,
            output,
            xform_in,
            buffer,
            min_points,
            bias_out,
            verbose,
        )
        return

    # The N&K regression needs broad stable terrain with slope variation; the
    # flat PGCP features used for the PGCP step are unsuitable, so require a
    # user-supplied stable mask for the nk and nk_icp methods.
    if method in ("nk", "nk_icp") and not stable_mask:
        gs.fatal(
            _(
                "method={m} requires a stable_mask of broad, sloped, unchanged "
                "terrain. PGCP features are too flat for the Nuth & Kaeaeb "
                "regression."
            ).format(m=method)
        )

    pid = os.getpid()
    tmp_pgcp = f"tmp_rdemcoreg_pgcp_{pid}"
    tmp_nk = f"tmp_rdemcoreg_nk_{pid}"
    if method != "pgcp_vertical":
        TMP_RASTERS.append(tmp_pgcp)

    # Stage 1: PGCP vertical correction (always runs first).
    pgcp_stats = pgcp_vertical_correction(
        dem=dem,
        reference=reference,
        pgcp=pgcp,
        output=tmp_pgcp if method != "pgcp_vertical" else output,
        buffer=buffer,
        min_points=min_points,
        bias_output=bias_out,
        verbose=verbose,
    )

    zero_nk = {"dz": 0.0, "dx": 0.0, "dy": 0.0}
    zero_icp = {"tx": 0.0, "ty": 0.0, "tz": 0.0, "yaw": 0.0}

    if method == "pgcp_vertical":
        if xform_out:
            write_combined_transform(
                xform_out, method, pgcp_stats["median_bias"], zero_nk, zero_icp
            )
        gs.message(_("Method: pgcp_vertical - done."))
        return

    # PGCP vertical correction followed by ICP, skipping the N&K stage. The
    # stable_mask is optional here and only restricts ICP to stable terrain
    # when supplied.
    if method == "icp":
        icp_xform = gs.tempfile()
        icp_kwargs = dict(
            reference=reference,
            source=tmp_pgcp,
            output=output,
            transform_out=icp_xform,
            overwrite=gs.overwrite(),
        )
        if stable_mask:
            icp_kwargs["mask"] = stable_mask
        gs.run_command("r.dem.icp", **icp_kwargs)
        icp = {k: float(v) for k, v in read_keyval(icp_xform).items() if k in zero_icp}
        if xform_out:
            write_combined_transform(
                xform_out, method, pgcp_stats["median_bias"], zero_nk, icp
            )
        gs.message(_("Method: icp - done."))
        return

    # Stage 2: Nuth & Kaeaeb horizontal + vertical refinement on the
    # PGCP-corrected DSM, capturing the solved offsets.
    nk_out = output if method == "nk" else tmp_nk
    if nk_out == tmp_nk:
        TMP_RASTERS.extend([tmp_nk, f"{tmp_nk}_resid"])
    nk_xform = gs.tempfile()
    gs.run_command(
        "r.dem.nk",
        sfm=tmp_pgcp,
        lidar=reference,
        stable_mask=stable_mask,
        output=nk_out,
        transform_output=nk_xform,
        overwrite=gs.overwrite(),
    )
    nk = {k: float(v) for k, v in read_keyval(nk_xform).items() if k in zero_nk}

    # Stage 3: ICP refinement of the N&K result, capturing its transform.
    icp = dict(zero_icp)
    if method == "nk_icp":
        icp_xform = gs.tempfile()
        gs.run_command(
            "r.dem.icp",
            reference=reference,
            source=tmp_nk,
            output=output,
            mask=stable_mask,
            transform_out=icp_xform,
            overwrite=gs.overwrite(),
        )
        icp = {k: float(v) for k, v in read_keyval(icp_xform).items() if k in zero_icp}

    if xform_out:
        write_combined_transform(xform_out, method, pgcp_stats["median_bias"], nk, icp)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
