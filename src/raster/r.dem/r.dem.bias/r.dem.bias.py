#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.bias
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Remove terrain-correlated systematic bias from a DEM of
#            Difference (DoD) that survives rigid co-registration, via local
#            trimmed-median (forest) or multivariable terrain regression.
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Remove terrain-correlated systematic bias from a DoD
# % keyword: raster
# % keyword: DEM
# % keyword: bias
# % keyword: change detection
# % keyword: regression
# %end

# %option G_OPT_R_INPUT
# % key: dod
# % description: Input DEM of Difference raster to correct
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output bias-corrected DoD raster
# % required: yes
# %end

# %option
# % key: method
# % type: string
# % required: yes
# % options: regression,forest
# % description: Bias-correction method
# %end

# %option G_OPT_R_INPUTS
# % key: predictors
# % description: Terrain predictor rasters (method=regression)
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: stable_mask
# % description: Stable-terrain mask defining the regression fit region (method=regression)
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: mask
# % description: Mask of cells used for the local bias field, e.g. forest (method=forest)
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: bias_field
# % description: Optional output of the estimated bias field that was subtracted
# % required: no
# %end

# %option
# % key: window
# % type: integer
# % answer: 21
# % description: Window size in cells for the local bias field (method=forest)
# % required: no
# %end

# %option
# % key: trim_low
# % type: double
# % answer: 2.5
# % description: Lower trimming percentile for the local bias core (method=forest)
# % required: no
# %end

# %option
# % key: trim_high
# % type: double
# % answer: 97.5
# % description: Upper trimming percentile for the local bias core (method=forest)
# % required: no
# %end

import atexit
import os
import sys

import grass.script as gs

TMP_RASTERS = []


def cleanup():
    if TMP_RASTERS:
        gs.run_command(
            "g.remove",
            type="raster",
            name=",".join(TMP_RASTERS),
            flags="f",
            quiet=True,
        )


def pearsons_coeff(raster):
    """Pearson's second skewness coefficient: 3 * (mean - median) / stddev."""
    univar = gs.parse_command("r.univar", map=raster, format="json", flags="e")
    mean = float(univar["mean"])
    median = float(univar["median"])
    stddev = float(univar["stddev"])
    if stddev == 0:
        return 0.0
    return 3.0 * (mean - median) / stddev


def zscore(raster, output, log=False):
    """Standardize a raster to zero mean and unit variance, optionally on a
    log scale for strongly skewed positive predictors.
    """
    src = raster
    if log:
        stats = gs.parse_command("r.univar", map=raster, format="json")
        if float(stats["min"]) <= 0:
            gs.warning(
                _(
                    "Cannot log-transform <{}> (non-positive values); "
                    "using linear scale"
                ).format(raster)
            )
        else:
            tmp_log = f"tmp_rdembias_log_{output}_{os.getpid()}"
            TMP_RASTERS.append(tmp_log)
            gs.mapcalc(f"{tmp_log} = log({raster})", overwrite=True, quiet=True)
            src = tmp_log

    univar = gs.parse_command("r.univar", map=src, format="json")
    mean = float(univar["mean"])
    stddev = float(univar["stddev"])
    if stddev == 0:
        gs.fatal(_("Predictor <{}> has zero variance").format(raster))
    gs.mapcalc(
        f"{output} = ({src} - {mean}) / {stddev}",
        overwrite=True,
        quiet=True,
    )
    return output


def correct_regression(dod, output, predictors, stable_mask, bias_field):
    """Fit a multivariable linear model of the DoD on z-scored terrain
    predictors over stable terrain, then subtract the fitted surface.
    """
    if not predictors:
        gs.fatal(_("Option predictors is required for method=regression"))
    if not stable_mask:
        gs.fatal(_("Option stable_mask is required for method=regression"))

    # Dependent variable: DoD restricted to stable terrain.
    stable_dod = f"tmp_rdembias_stable_dod_{os.getpid()}"
    TMP_RASTERS.append(stable_dod)
    gs.mapcalc(
        f"{stable_dod} = if(!isnull({stable_mask}), {dod}, null())",
        overwrite=True,
        quiet=True,
    )

    # Z-score each predictor, log-transforming strongly skewed ones.
    zmaps = []
    for pred in predictors:
        skew = pearsons_coeff(pred)
        use_log = abs(skew) > 0.75
        zname = f"tmp_rdembias_z_{pred.replace('@', '_')}_{os.getpid()}"
        TMP_RASTERS.append(zname)
        zscore(pred, zname, log=use_log)
        zmaps.append(zname)
        gs.message(_("Predictor <{}>: skew={:.3f} log={}").format(pred, skew, use_log))

    coeff = gs.parse_command(
        "r.regression.multi",
        mapx=zmaps,
        mapy=stable_dod,
        format="json",
    )
    intercept = float(coeff["b0"])
    by_name = {p["name"]: float(p["b"]) for p in coeff["predictors"]}

    terms = " + ".join(f"{by_name[z]} * {z}" for z in zmaps)
    field = bias_field or f"tmp_rdembias_fit_{os.getpid()}"
    if not bias_field:
        TMP_RASTERS.append(field)
    gs.mapcalc(f"{field} = {intercept} + {terms}", overwrite=gs.overwrite())
    gs.mapcalc(f"{output} = {dod} - {field}", overwrite=gs.overwrite())

    gs.message(_("Regression intercept b0 = {:.4f}").format(intercept))
    for z, b in by_name.items():
        gs.message(_("  {}: b = {:.4f}").format(z, b))


def correct_forest(dod, output, mask, window, trim_low, trim_high, bias_field):
    """Estimate a local trimmed-median bias field over the masked cells (e.g.
    a forest canopy bump) and subtract it from the DoD.
    """
    if not mask:
        gs.fatal(_("Option mask is required for method=forest"))
    if window < 3 or window % 2 == 0:
        gs.fatal(_("Option window must be an odd integer >= 3"))

    with gs.MaskManager(mask):
        quants = gs.parse_command(
            "r.univar",
            map=dod,
            percentile=[trim_low, trim_high],
            format="json",
            flags="e",
        )["percentiles"]
        lo = next(q["value"] for q in quants if q["percentile"] == trim_low)
        hi = next(q["value"] for q in quants if q["percentile"] == trim_high)

        core = f"tmp_rdembias_core_{os.getpid()}"
        TMP_RASTERS.append(core)
        gs.mapcalc(
            f"{core} = if({dod} >= {lo} && {dod} <= {hi}, {dod}, null())",
            overwrite=True,
            quiet=True,
        )
        local_med = f"tmp_rdembias_local_med_{os.getpid()}"
        TMP_RASTERS.append(local_med)
        gs.run_command(
            "r.neighbors",
            input=core,
            output=local_med,
            method="median",
            size=window,
            overwrite=True,
            quiet=True,
        )

    # Outside the mask the bias field is zero (no correction). Clamp explicitly
    # to the mask so the moving-window median cannot leak across the boundary.
    field = bias_field or f"tmp_rdembias_field_{os.getpid()}"
    if not bias_field:
        TMP_RASTERS.append(field)
    gs.mapcalc(
        f"{field} = if(isnull({mask}) || isnull({local_med}), 0, {local_med})",
        overwrite=gs.overwrite(),
    )
    gs.mapcalc(f"{output} = {dod} - {field}", overwrite=gs.overwrite())
    gs.message(
        _("Forest bias field estimated over <{}> (window={})").format(mask, window)
    )


def main():
    dod = options["dod"]
    output = options["output"]
    method = options["method"]
    predictors = options["predictors"].split(",") if options["predictors"] else []
    stable_mask = options["stable_mask"]
    mask = options["mask"]
    bias_field = options["bias_field"]
    window = int(options["window"])
    trim_low = float(options["trim_low"])
    trim_high = float(options["trim_high"])

    if not gs.find_file(dod, element="raster")["name"]:
        gs.fatal(_("Raster map <{}> not found").format(dod))

    if method == "regression":
        correct_regression(dod, output, predictors, stable_mask, bias_field)
    else:
        correct_forest(dod, output, mask, window, trim_low, trim_high, bias_field)

    gs.run_command(
        "r.support",
        map=output,
        title=f"Bias-corrected DoD ({method})",
        units="metres",
    )
    gs.message(_("Bias-corrected DoD written: <{}>").format(output))
    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
