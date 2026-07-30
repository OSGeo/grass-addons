#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.lod
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Compute Level of Detection (LoD) for DEM differencing.
#
# COPYRIGHT: (C) 2025-2026 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Compute Level of Detection (LoD) for DEM difference maps
# % keyword: raster
# % keyword: statistics
# % keyword: uncertainty
# % keyword: DEM
# % keyword: change detection
# %end

# %option G_OPT_R_INPUT
# % key: dem
# % description: Post-event DEM (co-registered)
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % key: reference
# % description: Reference DEM
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output LoD raster
# % required: yes
# %end

# %option
# % key: method
# % type: string
# % options: global,local
# % answer: local
# % description: LoD method: global (uniform) or local (spatially variable)
# % required: yes
# %end

# %option
# % key: confidence
# % type: double
# % answer: 0.95
# % description: Confidence level (e.g., 0.95 for 95% CI)
# % required: no
# %end

# %option
# % key: window
# % type: integer
# % answer: 21
# % description: Moving window size (cells) for local LoD, must be odd
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: point_density
# % description: Point cloud density raster (pts per square meter), used in local LoD
# % required: no
# %end

# %option
# % key: nmad
# % type: double
# % description: Pre-computed NMAD (m), skips stable pixel estimation if provided
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: stable_mask
# % description: Raster mask of stable pixels for sigma estimation (1=stable, null=unstable)
# % required: no
# %end

import atexit
import sys
import os

import numpy as np
from scipy.stats import norm as scipy_norm

import grass.script as gs

TMP_PREFIX = f"tmp_rdemlod_{os.getpid()}"


def cleanup():
    gs.run_command(
        "g.remove", type="raster", pattern=f"{TMP_PREFIX}*", flags="f", quiet=True
    )


def raster_median(map_name):
    """Median of a raster via r.univar extended statistics."""
    stats = gs.parse_command("r.univar", map=map_name, flags="ge")
    if "median" not in stats:
        gs.fatal(_("Unable to compute median of <{}>").format(map_name))
    return float(stats["median"])


def estimate_nmad(dem, reference, stable_mask):
    """
    Estimate NMAD from stable pixels by differencing DEM and reference.
    NMAD = 1.4826 * median(|dh - median(dh)|) on stable terrain.
    """
    diff_map = f"{TMP_PREFIX}_diff_stable"
    if stable_mask:
        gs.mapcalc(
            f"{diff_map} = if(!isnull({stable_mask}), {dem} - {reference}, null())",
            overwrite=True,
            quiet=True,
        )
    else:
        gs.mapcalc(f"{diff_map} = {dem} - {reference}", overwrite=True, quiet=True)

    median_dh = raster_median(diff_map)

    # NMAD via r.mapcalc abs deviation then median
    abs_dev = f"{TMP_PREFIX}_abs_dev"
    gs.mapcalc(f"{abs_dev} = abs({diff_map} - {median_dh})", overwrite=True, quiet=True)
    mad = raster_median(abs_dev)
    nmad = 1.4826 * mad

    gs.run_command(
        "g.remove", type="raster", name=f"{diff_map},{abs_dev}", flags="f", quiet=True
    )
    return nmad


def global_lod(dem, reference, output, confidence, nmad_val):
    """
    Global LoD: uniform sigma across the study area.
    LoD = t_conf * sqrt(2) * sigma
    where sigma = NMAD / 1.4826 (robust estimate of standard deviation)
    """
    t = scipy_norm.ppf((1 + confidence) / 2)
    sigma = nmad_val / 1.4826
    lod_val = t * np.sqrt(2) * sigma

    gs.message(_("Global LoD ({:.0f}% CI):").format(confidence * 100))
    gs.message(_("  NMAD:  {:.4f} m").format(nmad_val))
    gs.message(_("  sigma: {:.4f} m").format(sigma))
    gs.message(_("  t:     {:.4f}").format(t))
    gs.message(_("  LoD:   {:.4f} m  (uniform)").format(lod_val))

    gs.mapcalc(f"{output} = {lod_val}", overwrite=gs.overwrite())
    gs.run_command(
        "r.support",
        map=output,
        title=f"Global LoD {confidence * 100:.0f}% CI = {lod_val:.4f} m",
        units="metres",
    )
    return lod_val


def local_lod(dem, reference, output, confidence, window, point_density, stable_mask):
    """
    Local spatially-variable LoD using moving-window MAD.

    sigma_local(x,y) = 1.4826 * median(|dh - median(dh)|) in window W
    LoD(x,y) = t * sqrt(2) * sigma_local(x,y)

    Optionally penalised by low point cloud density:
    sigma_local_adj = sigma_local * (1 + k / max(point_density, eps))
    where k is an empirical density penalty coefficient.
    """
    t = scipy_norm.ppf((1 + confidence) / 2)
    win = int(window)
    if win % 2 == 0:
        win += 1
        gs.warning(_("Window must be odd, adjusted to {}").format(win))

    diff_map = f"{TMP_PREFIX}_diff_full"

    if stable_mask:
        gs.mapcalc(
            f"{diff_map} = if(!isnull({stable_mask}), {dem} - {reference}, null())",
            overwrite=True,
            quiet=True,
        )
    else:
        gs.mapcalc(f"{diff_map} = {dem} - {reference}", overwrite=True, quiet=True)

    # Local median of dh
    median_local = f"{TMP_PREFIX}_median_local"
    gs.run_command(
        "r.neighbors",
        input=diff_map,
        output=median_local,
        method="median",
        size=win,
        overwrite=True,
        quiet=True,
    )

    # Local MAD: |dh - local_median|
    abs_dev_local = f"{TMP_PREFIX}_abs_dev_local"
    gs.mapcalc(
        f"{abs_dev_local} = abs({diff_map} - {median_local})",
        overwrite=True,
        quiet=True,
    )

    # Local MAD via moving window median
    mad_local = f"{TMP_PREFIX}_mad_local"
    gs.run_command(
        "r.neighbors",
        input=abs_dev_local,
        output=mad_local,
        method="median",
        size=win,
        overwrite=True,
        quiet=True,
    )

    # NMAD_local = 1.4826 * MAD_local
    nmad_local = f"{TMP_PREFIX}_nmad_local"
    gs.mapcalc(f"{nmad_local} = 1.4826 * {mad_local}", overwrite=True, quiet=True)

    # Density penalty (optional)
    if point_density and gs.find_file(point_density, element="raster")["name"]:
        density_pen = f"{TMP_PREFIX}_density_pen"
        k = 0.5  # empirical penalty coefficient, tunable
        eps = 0.1
        gs.mapcalc(
            f"{density_pen} = {nmad_local} * (1.0 + {k} / max({point_density}, {eps}))",
            overwrite=True,
            quiet=True,
        )
        nmad_src = density_pen
        gs.message(_("Point density penalty applied (k={})").format(k))
    else:
        nmad_src = nmad_local

    # sigma_local = NMAD_local / 1.4826
    # LoD = t * sqrt(2) * sigma_local, floored at 0.01 m
    gs.mapcalc(
        f"{output} = max({t} * sqrt(2.0) * ({nmad_src} / 1.4826), 0.01)",
        overwrite=gs.overwrite(),
    )

    gs.run_command(
        "r.support",
        map=output,
        title=f"Local LoD {confidence * 100:.0f}% CI (window={win} cells)",
        units="metres",
    )

    # Report stats
    stats = gs.parse_command("r.univar", map=output, flags="ge")
    gs.message(_("Local LoD stats:"))
    gs.message(_("  Min:  {:.4f} m").format(float(stats.get("min", 0))))
    gs.message(_("  Mean: {:.4f} m").format(float(stats.get("mean", 0))))
    gs.message(_("  Max:  {:.4f} m").format(float(stats.get("max", 0))))
    gs.message(_("  CV:   {:.1f}%").format(float(stats.get("coeff_var", 0))))


def main():
    dem = options["dem"]
    reference = options["reference"]
    output = options["output"]
    method = options["method"]
    confidence = float(options["confidence"])
    window = int(options["window"])
    point_density = options.get("point_density", "")
    nmad_pre = options.get("nmad", "")
    stable_mask = options.get("stable_mask", "")

    # Get or compute NMAD
    if nmad_pre:
        nmad_val = float(nmad_pre)
        gs.message(_("Using pre-computed NMAD: {:.4f} m").format(nmad_val))
    else:
        gs.message(_("Estimating NMAD from stable pixels..."))
        nmad_val = estimate_nmad(dem, reference, stable_mask)
        gs.message(_("Estimated NMAD: {:.4f} m").format(nmad_val))

    if method == "global":
        global_lod(dem, reference, output, confidence, nmad_val)
    else:
        local_lod(
            dem,
            reference,
            output,
            confidence,
            window,
            point_density,
            stable_mask,
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
