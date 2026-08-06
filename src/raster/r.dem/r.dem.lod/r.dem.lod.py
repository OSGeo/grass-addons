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
# % description: Post-event DEM (co-registered); requires reference
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: reference
# % description: Reference DEM; requires dem
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: dod
# % description: Precomputed (e.g. debiased) DEM of Difference; alternative to dem+reference
# % required: no
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

# %option
# % key: floor
# % type: double
# % answer: 0.0
# % description: Flight-wide stable-residual NMAD (meters, 1 sigma); its long-wavelength excess over the windowed dispersion is added once (two-scale decomposition)
# % required: no
# %end

# %option
# % key: min_stable
# % type: integer
# % answer: 25
# % description: Minimum stable cells inside the window for the local dispersion to be defined (guards the sparse-coverage sigma_win=0 degeneracy)
# % required: no
# %end

# %option G_OPT_R_INPUTS
# % key: sigma_extra
# % description: Additional 1-sigma uncertainty rasters added in quadrature
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output_sigma
# % description: Output combined 1-sigma uncertainty raster (output = z * this)
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output_domain
# % description: Output significance-domain raster (1 = LoD defined, NULL elsewhere; method=local)
# % required: no
# %end

# %rules
# % required: dod, dem
# % exclusive: dod, dem
# % requires: dem, reference
# % requires: reference, dem
# %end

import atexit
import math
import sys
import os

import grass.script as gs

TMP_PREFIX = f"tmp_rdemlod_{os.getpid()}"


def cleanup():
    gs.run_command(
        "g.remove", type="raster", pattern=f"{TMP_PREFIX}*", flags="f", quiet=True
    )


def z_from_confidence(confidence):
    """Two-tailed normal critical value; scipy imported lazily so the tool
    can print its interface without scipy installed."""
    try:
        from scipy.stats import norm
    except ImportError:
        gs.fatal(_("r.dem.lod requires scipy"))
    return float(norm.ppf((1 + confidence) / 2))


def gaussian_weighting_factor(window):
    """Gaussian weighting factor for r.neighbors, matching r.dem.stats so
    the windowed dispersion estimators are numerically comparable."""
    return (window - 1) / 2 * 0.5


def build_residual(dod, dem, reference, stable_mask, output):
    """Residual map for dispersion estimation: the DoD (or dem - reference),
    optionally restricted to stable cells."""
    src = dod if dod else f"{dem} - {reference}"
    if stable_mask:
        expr = f"{output} = if(!isnull({stable_mask}), {src}, null())"
    else:
        expr = f"{output} = {src}"
    gs.mapcalc(expr, overwrite=True, quiet=True)
    return output


def raster_median(map_name):
    """Median of a raster via r.univar extended statistics."""
    stats = gs.parse_command("r.univar", map=map_name, flags="ge")
    if "median" not in stats:
        gs.fatal(_("Unable to compute median of <{}>").format(map_name))
    return float(stats["median"])


def estimate_nmad(dod, dem, reference, stable_mask):
    """
    Estimate NMAD of the residual (DoD or dem - reference) on stable pixels.
    NMAD = 1.4826 * median(|dh - median(dh)|) on stable terrain.
    """
    diff_map = f"{TMP_PREFIX}_diff_stable"
    build_residual(dod, dem, reference, stable_mask, diff_map)

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


def global_lod(output, confidence, nmad_val, floor):
    """
    Global LoD: uniform sigma across the study area.

    LoD = z * sqrt(NMAD^2 + floor^2)

    The NMAD of the stable residual population is already a robust estimate
    of the difference sigma (both input paths difference the surfaces before
    estimation), so no sqrt(2) epoch factor and no /1.4826 rescaling apply.
    A non-zero floor here must be an INDEPENDENT registration budget, not
    the same population's NMAD, or the two terms double-count.
    """
    z = z_from_confidence(confidence)
    if floor > 0.0 and abs(floor - nmad_val) < 1e-9:
        gs.warning(
            _(
                "floor equals nmad: the floor must come from an independent "
                "registration budget or the two terms double-count"
            )
        )
    sigma = nmad_val
    lod_val = z * math.sqrt(sigma**2 + floor**2)

    gs.message(_("Global LoD ({:.0f}% CI):").format(confidence * 100))
    gs.message(_("  NMAD:  {:.4f} m").format(nmad_val))
    gs.message(_("  sigma: {:.4f} m").format(sigma))
    gs.message(_("  z:     {:.4f}").format(z))
    gs.message(_("  LoD:   {:.4f} m  (uniform)").format(lod_val))

    gs.mapcalc(f"{output} = {lod_val}", overwrite=gs.overwrite())
    gs.run_command(
        "r.support",
        map=output,
        title=f"Global LoD {confidence * 100:.0f}% CI = {lod_val:.4f} m",
        units="metres",
    )
    return lod_val


def local_lod(
    dod,
    dem,
    reference,
    output,
    confidence,
    window,
    point_density,
    stable_mask,
    floor,
    min_stable,
    sigma_extra,
    output_sigma,
    output_domain,
):
    """
    Local spatially-variable LoD from a moving-window MAD of the residual
    over stable cells (Gaussian-weighted, matching r.dem.stats):

      sigma_win(x,y) = 1.4826 * median_W(|dh - median_W(dh)|)

    Both input paths difference the surfaces before windowing, so the
    windowed NMAD estimates the difference sigma directly on either path
    and no sqrt(2) epoch factor applies:

      LoD(x,y) = z * sqrt(sigma_win^2 + s_long^2 + sum(sigma_extra_i^2))

    where s_long^2 = max(0, floor^2 - median_stable(sigma_win^2)) is the
    long-wavelength excess of the flight-wide stable NMAD over the windowed
    dispersion, added once (adding floor^2 in quadrature would double-count
    the short-wavelength component and turn a nominal 95% limit into ~99%).

    The LoD is defined only within the window's reach of stable cells; it is
    NOT extended beyond (coefficient-style uncertainty cannot express
    model-form error under extrapolation, so extension requires an
    out-of-sample envelope; see the manual). Coverage is always reported.

    Optionally penalised by low point cloud density:
    sigma_win_adj = sigma_win * (1 + k / max(point_density, eps))
    """
    z = z_from_confidence(confidence)
    win = int(window)
    if win % 2 == 0:
        win += 1
        gs.warning(_("Window must be odd, adjusted to {}").format(win))
    wf = gaussian_weighting_factor(win)

    diff_map = f"{TMP_PREFIX}_diff_full"
    build_residual(dod, dem, reference, stable_mask, diff_map)

    # Local median of dh (Gaussian-weighted, matching r.dem.stats)
    median_local = f"{TMP_PREFIX}_median_local"
    gs.run_command(
        "r.neighbors",
        input=diff_map,
        output=median_local,
        method="median",
        size=win,
        weighting_function="gaussian",
        weighting_factor=wf,
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

    mad_local = f"{TMP_PREFIX}_mad_local"
    gs.run_command(
        "r.neighbors",
        input=abs_dev_local,
        output=mad_local,
        method="median",
        size=win,
        weighting_function="gaussian",
        weighting_factor=wf,
        overwrite=True,
        quiet=True,
    )

    # sigma_win = NMAD_local = 1.4826 * MAD_local, defined only where the
    # window holds at least min_stable stable cells: with very few cells the
    # windowed median degenerates (a single cell gives sigma_win exactly 0).
    stable_count = f"{TMP_PREFIX}_stable_count"
    gs.run_command(
        "r.neighbors",
        input=diff_map,
        output=stable_count,
        method="count",
        size=win,
        overwrite=True,
        quiet=True,
    )
    sigma_win = f"{TMP_PREFIX}_sigma_win"
    gs.mapcalc(
        f"{sigma_win} = if({stable_count} >= {min_stable}, "
        f"1.4826 * {mad_local}, null())",
        overwrite=True,
        quiet=True,
    )

    # Density penalty (optional). NULL in the density raster propagates:
    # cells with unknown uncertainty are untestable.
    if point_density and not gs.find_file(point_density, element="raster")["name"]:
        gs.fatal(_("point_density raster <{}> not found").format(point_density))
    if point_density:
        density_pen = f"{TMP_PREFIX}_density_pen"
        k = 0.5  # empirical penalty coefficient, tunable
        eps = 0.1
        gs.mapcalc(
            f"{density_pen} = {sigma_win} * (1.0 + {k} / max({point_density}, {eps}))",
            overwrite=True,
            quiet=True,
        )
        sigma_win = density_pen
        gs.message(_("Point density penalty applied (k={})").format(k))

    # Two-scale decomposition of the flight-wide NMAD (floor): the windowed
    # NMAD estimates the short-wavelength component; the flight-wide stable
    # NMAD estimates the total. Adding the floor in quadrature would count
    # the short-wavelength component twice (inflating a nominal 95% LoD to
    # roughly 99%), so only the long-wavelength excess is added once:
    #   s_long^2 = max(0, floor^2 - median_stable(sigma_win^2))
    # Both input paths estimate the DIFFERENCE dispersion directly (the
    # residual is differenced before windowing), so no sqrt(2) epoch factor
    # applies on either path.
    s_long2 = 0.0
    if floor > 0.0:
        sq = f"{TMP_PREFIX}_sigwin_sq"
        if stable_mask:
            gs.mapcalc(
                f"{sq} = if(!isnull({stable_mask}), pow({sigma_win}, 2), "
                f"null())",
                overwrite=True,
                quiet=True,
            )
        else:
            gs.mapcalc(
                f"{sq} = pow({sigma_win}, 2)", overwrite=True, quiet=True
            )
        med_sq = raster_median(sq)
        s_long2 = max(0.0, floor**2 - med_sq)
        gs.message(
            _(
                "Two-scale decomposition: floor={:.4f} m, "
                "median windowed sigma={:.4f} m, long-wavelength "
                "component s_long={:.4f} m (added once)"
            ).format(floor, math.sqrt(med_sq), math.sqrt(s_long2))
        )
        if s_long2 == 0.0:
            gs.warning(
                _(
                    "The windowed dispersion already exceeds the floor "
                    "({:.4f} m): the long-wavelength term is zero and the "
                    "floor contributes nothing"
                ).format(floor)
            )

    # NULL propagates from sigma_win (beyond window reach or below
    # min_stable) AND from any sigma_extra raster: a cell whose uncertainty
    # is unknown is untestable.
    terms = [f"pow({sigma_win}, 2)"]
    if s_long2 > 0.0:
        terms.append(f"{s_long2:.17g}")
    for extra in sigma_extra:
        terms.append(f"pow({extra}, 2)")
    sigma_comb = output_sigma or f"{TMP_PREFIX}_sigma_comb"
    gs.mapcalc(
        f"{sigma_comb} = sqrt({' + '.join(terms)})",
        overwrite=gs.overwrite() if output_sigma else True,
    )
    if output_sigma:
        gs.run_command(
            "r.support",
            map=sigma_comb,
            title="Combined 1-sigma uncertainty (windowed + floor + extra)",
            units="metres",
            description=(
                f"window={win} floor={floor} s_long2={s_long2:.6g} "
                f"min_stable={min_stable}"
            ),
        )

    # Restrict the LoD to the observation footprint: the r.neighbors
    # dilation must not define a detection limit over unobserved cells.
    obs_cond = (
        f"!isnull({dod})" if dod
        else f"(!isnull({dem}) && !isnull({reference}))"
    )
    gs.mapcalc(
        f"{output} = if({obs_cond}, {z} * {sigma_comb}, null())",
        overwrite=gs.overwrite(),
    )
    gs.run_command(
        "r.support",
        map=output,
        title=f"Local LoD {confidence * 100:.0f}% CI (window={win} cells, "
        f"floor={floor} m)",
        units="metres",
    )

    # Significance domain: 1 where the (observation-restricted) LoD exists.
    if output_domain:
        gs.mapcalc(
            f"{output_domain} = if(!isnull({output}), 1, null())",
            overwrite=gs.overwrite(),
        )
        gs.run_command(
            "r.support",
            map=output_domain,
            title="LoD significance domain (1 = testable)",
        )
        gs.write_command(
            "r.category",
            map=output_domain,
            rules="-",
            separator=":",
            stdin="1:LoD defined (testable)\n",
        )

    if floor <= 0.0:
        sw_min = float(
            gs.parse_command("r.univar", map=sigma_win, flags="g").get(
                "min", 0.0
            )
        )
        if sw_min <= 0.0:
            gs.warning(
                _(
                    "floor=0 and the windowed sigma reaches 0: cells with "
                    "degenerate local dispersion get LoD 0; supply a floor"
                )
            )

    # Coverage report (always): tested share of observed cells.
    obs_map = f"{TMP_PREFIX}_obs"
    gs.mapcalc(
        f"{obs_map} = if({obs_cond}, 1, null())", overwrite=True, quiet=True
    )
    n_obs = int(gs.parse_command("r.univar", map=obs_map, flags="g").get("n", 0))
    stats = gs.parse_command("r.univar", map=output, flags="ge")
    n_lod = int(stats.get("n", 0))
    pct = 100.0 * n_lod / n_obs if n_obs else 0.0
    gs.message(_("Significance domain: {} of {} observed cells ({:.1f}%)").format(
        n_lod, n_obs, pct
    ))
    gs.message(_("Local LoD stats:"))
    gs.message(_("  Min:  {:.4f} m").format(float(stats.get("min", 0))))
    gs.message(_("  Mean: {:.4f} m").format(float(stats.get("mean", 0))))
    gs.message(_("  Max:  {:.4f} m").format(float(stats.get("max", 0))))
    gs.message(_("  CV:   {:.1f}%").format(float(stats.get("coeff_var", 0))))


def main():
    dem = options["dem"]
    reference = options["reference"]
    dod = options["dod"]
    output = options["output"]
    method = options["method"]
    confidence = float(options["confidence"])
    window = int(options["window"])
    point_density = options.get("point_density", "")
    nmad_pre = options.get("nmad", "")
    stable_mask = options.get("stable_mask", "")
    floor = float(options["floor"]) if options["floor"] else 0.0
    min_stable = int(options["min_stable"])
    if floor < 0.0:
        gs.fatal(_("Option floor must be non-negative"))
    if not 0.0 < confidence < 1.0:
        gs.fatal(_("Option confidence must be strictly between 0 and 1"))
    sigma_extra = (
        options["sigma_extra"].split(",") if options["sigma_extra"] else []
    )
    output_sigma = options["output_sigma"]
    output_domain = options["output_domain"]

    if method == "global":
        if nmad_pre:
            nmad_val = float(nmad_pre)
            gs.message(_("Using pre-computed NMAD: {:.4f} m").format(nmad_val))
        else:
            gs.message(_("Estimating NMAD from stable pixels..."))
            nmad_val = estimate_nmad(dod, dem, reference, stable_mask)
            gs.message(_("Estimated NMAD: {:.4f} m").format(nmad_val))
        if sigma_extra or output_sigma or output_domain or point_density:
            gs.warning(
                _(
                    "Options sigma_extra/output_sigma/output_domain/"
                    "point_density are ignored for method=global"
                )
            )
        global_lod(output, confidence, nmad_val, floor)
    else:
        if nmad_pre:
            gs.warning(_("Option nmad is ignored for method=local"))
        local_lod(
            dod,
            dem,
            reference,
            output,
            confidence,
            window,
            point_density,
            stable_mask,
            floor,
            min_stable,
            sigma_extra,
            output_sigma,
            output_domain,
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
