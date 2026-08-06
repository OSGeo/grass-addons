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
# % options: regression,forest,spline
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

# %option G_OPT_R_OUTPUT
# % key: output_se
# % description: Output coefficient-uncertainty SE raster of the bias model, sqrt(x' Cov x) (method=regression, 1 sigma, excludes residual variance)
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output_leverage
# % description: Output extrapolation-distance raster d = sqrt(n*h - 1) in fit-sd units (method=regression)
# % required: no
# %end

# %option G_OPT_F_OUTPUT
# % key: fit_json
# % description: JSON file persisting the fit (n, s2, coefficients, covariance, transforms; method=regression)
# % required: no
# %end

# %option
# % key: spline_tension
# % type: double
# % answer: 40.0
# % description: v.surf.rst tension for the spline bias field (method=spline)
# % required: no
# %end

# %option
# % key: spline_smooth
# % type: double
# % answer: 5.0
# % description: v.surf.rst smoothing for the spline bias field (method=spline; oversmoothing is the safe direction for a long-wavelength field)
# % required: no
# %end

# %option
# % key: spline_npoints
# % type: integer
# % answer: 50000
# % description: Stable cells sampled as spline fit points (method=spline; deterministic seed)
# % required: no
# %end

# %option
# % key: spline_res
# % type: double
# % answer: 10.0
# % description: Interpolation resolution (m) for the spline bias field, resampled bilinearly to the analysis grid (method=spline)
# % required: no
# %end

# %option
# % key: log_predictors
# % type: string
# % multiple: yes
# % description: Predictors to log-transform before z-scoring (must be listed in predictors; explicit, never data-triggered)
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
    return output, mean, stddev


MAX_FIT_CELLS = 2_000_000


def sample_stable_cells(stable_dod, zmaps):
    """Stream (dod, z1..zk) rows over stable cells into a numpy array.

    Uses r.stats -1n, skipping any row that still carries a NULL marker,
    so the fit sees only cells where the DoD and every predictor are
    defined.
    """
    try:
        import numpy as np
    except ImportError:
        gs.fatal(_("method=regression requires numpy"))

    proc = gs.pipe_command(
        "r.stats",
        input=",".join([stable_dod] + zmaps),
        flags="1n",
        separator=",",
        quiet=True,
    )

    def valid_lines():
        # grass.script Popen pipes are text-mode (text=True).
        for line in proc.stdout:
            if "*" in line:
                continue
            yield line

    data = np.loadtxt(valid_lines(), delimiter=",", ndmin=2)
    if proc.wait() != 0:
        gs.fatal(_("r.stats failed while sampling stable cells"))
    if data.size == 0:
        gs.fatal(_("No valid stable cells found for the regression fit"))
    return data


def fit_ols(data):
    """OLS fit with covariance: returns (beta, s2, cov, n).

    beta[0] is the intercept; s2 is the residual variance (prediction
    interval term); cov is the coefficient covariance s2 * (X'X)^-1.
    Subsamples deterministically above MAX_FIT_CELLS so reruns reproduce
    coefficients exactly.
    """
    import numpy as np

    n_total = data.shape[0]
    if n_total > MAX_FIT_CELLS:
        rng = np.random.default_rng(42)
        idx = rng.choice(n_total, MAX_FIT_CELLS, replace=False)
        data = data[idx]
        gs.message(
            _("Subsampled {} of {} stable cells (seed 42)").format(
                MAX_FIT_CELLS, n_total
            )
        )
    y = data[:, 0]
    X = np.column_stack([np.ones(data.shape[0]), data[:, 1:]])
    n, p = X.shape
    if n <= p:
        gs.fatal(_("Too few stable cells ({}) for {} coefficients").format(n, p))
    xtx = X.T @ X
    # A near-singular design zeroes variance in exactly the direction
    # extrapolation excites, so it is a hard stop rather than a silent
    # pseudo-inverse fallback.
    if np.linalg.cond(xtx) > 1e10:
        gs.fatal(
            _(
                "Predictor matrix is near-singular (collinear predictors); "
                "remove or combine collinear predictors"
            )
        )
    xtx_inv = np.linalg.inv(xtx)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta
    s2 = float(resid @ resid) / (n - p)
    cov = s2 * xtx_inv
    return beta, s2, cov, n


def quad_expression(zmaps, matrix):
    """Mapcalc expression for the quadratic form x' M x, x = [1, z1..zk].

    Evaluated per cell on the same transformed predictor rasters used in
    the fit; clamped at zero downstream against floating-point rounding.
    """
    x = ["1.0"] + list(zmaps)
    terms = []
    k = len(x)
    for i in range(k):
        for j in range(i, k):
            c = float(matrix[i, j]) * (1.0 if i == j else 2.0)
            factors = [f"({c:.17g})"]
            if x[i] != "1.0":
                factors.append(x[i])
            if x[j] != "1.0":
                factors.append(x[j])
            terms.append(" * ".join(factors))
    return " + ".join(terms)


def correct_regression(
    dod,
    output,
    predictors,
    stable_mask,
    bias_field,
    output_se,
    output_leverage,
    log_predictors,
    fit_json,
):
    """Fit a multivariable linear model of the DoD on z-scored terrain
    predictors over stable terrain, then subtract the fitted surface.

    The fit is a numpy OLS on sampled stable cells (replacing the earlier
    r.regression.multi call): the coefficient covariance is required for the
    prediction-SE output and must come from the same fit as the
    coefficients.
    """
    if not predictors:
        gs.fatal(_("Option predictors is required for method=regression"))
    if len(set(predictors)) != len(predictors):
        gs.fatal(_("Duplicate predictor rasters are not allowed"))
    if not stable_mask:
        gs.fatal(_("Option stable_mask is required for method=regression"))
    for name in log_predictors:
        if name not in predictors:
            gs.fatal(_("log_predictors entry <{}> is not in predictors").format(name))

    # Dependent variable: DoD restricted to stable terrain.
    stable_dod = f"tmp_rdembias_stable_dod_{os.getpid()}"
    TMP_RASTERS.append(stable_dod)
    gs.mapcalc(
        f"{stable_dod} = if(!isnull({stable_mask}), {dod}, null())",
        overwrite=True,
        quiet=True,
    )

    # Z-score each predictor; log transforms are explicit via
    # log_predictors, never data-triggered (a region-scoped skew statistic
    # crossing a threshold must not silently change the model form).
    zmaps = []
    transform_meta = []
    for pred in predictors:
        use_log = pred in log_predictors
        zname = f"tmp_rdembias_z_{pred.replace('@', '_')}_{os.getpid()}"
        TMP_RASTERS.append(zname)
        _zmap, zmean, zsd = zscore(pred, zname, log=use_log)
        zmaps.append(zname)
        transform_meta.append(f"{pred}: mean={zmean:.6g} sd={zsd:.6g} log={use_log}")
        gs.message(_("Predictor <{}>: log={}").format(pred, use_log))

    data = sample_stable_cells(stable_dod, zmaps)
    beta, s2, cov, n_fit = fit_ols(data)
    intercept = float(beta[0])
    coefs = {z: float(b) for z, b in zip(zmaps, beta[1:], strict=True)}

    terms = " + ".join(f"{b} * {z}" for z, b in coefs.items())
    field = bias_field or f"tmp_rdembias_fit_{os.getpid()}"
    if not bias_field:
        TMP_RASTERS.append(field)
    gs.mapcalc(f"{field} = {intercept} + {terms}", overwrite=gs.overwrite())
    gs.mapcalc(f"{output} = {dod} - {field}", overwrite=gs.overwrite())

    gs.message(_("OLS fit on {} stable cells").format(n_fit))
    gs.message(_("Regression intercept b0 = {:.4f}").format(intercept))
    for z, b in coefs.items():
        gs.message(_("  {}: b = {:.4f}").format(z, b))
    gs.message(_("Residual variance s2 = {:.4f} m^2").format(s2))

    if fit_json:
        import json

        with open(fit_json, "w") as f:
            json.dump(
                {
                    "n_fit": n_fit,
                    "s2_m2": s2,
                    "intercept": intercept,
                    "coefficients": {
                        pred: coefs[z]
                        for pred, z in zip(predictors, zmaps, strict=True)
                    },
                    "covariance": [list(map(float, row)) for row in cov],
                    "transforms": transform_meta,
                    "max_fit_cells": MAX_FIT_CELLS,
                },
                f,
                indent=2,
            )
        gs.message(_("Fit persisted to: {}").format(fit_json))

    fit_meta = (
        f"OLS n={n_fit}, s2={s2:.6g} m^2 (residual variance, iid assumption; "
        f"understates uncertainty under spatially correlated residuals); "
        + "; ".join(transform_meta)
    )
    gs.run_command("r.support", map=output, description=fit_meta)

    if output_se:
        quad = quad_expression(zmaps, cov)
        gs.mapcalc(
            f"{output_se} = sqrt(max(0.0, {quad}))",
            overwrite=gs.overwrite(),
        )
        gs.run_command(
            "r.support",
            map=output_se,
            title="Bias-model coefficient-uncertainty SE (1 sigma)",
            units="metres",
            description=fit_meta,
        )
        se_stats = gs.parse_command("r.univar", map=output_se, format="json")
        gs.message(
            _("Model SE range: {:.4g} to {:.4g} m (excludes s2)").format(
                float(se_stats["min"]), float(se_stats["max"])
            )
        )

    if output_leverage:
        import numpy as np

        xtx_inv = cov / s2
        h_quad = quad_expression(zmaps, np.asarray(xtx_inv))
        gs.mapcalc(
            f"{output_leverage} = sqrt(max(0.0, {n_fit} * ({h_quad}) - 1.0))",
            overwrite=gs.overwrite(),
        )
        gs.run_command(
            "r.support",
            map=output_leverage,
            title="Bias-model extrapolation distance (fit-sd units)",
            description=fit_meta,
        )


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


def correct_spline(dod, output, stable_mask, bias_field, tension, smooth, npoints, res):
    """Interpolate the stable-cell residuals into a smooth spatial bias
    field (v.surf.rst) and subtract it.

    Models the systematic error as what it is, a smooth surface over the
    map (e.g. photogrammetric doming), rather than a function of terrain
    predictors, avoiding the collinearity pathologies of the regression
    path. The field is fit at a coarse resolution (the error is
    long-wavelength) and resampled bilinearly to the analysis grid.
    Splines interpolate well and extrapolate poorly, so the correction is
    most trustworthy near the stable cells, which is where windowed
    detection limits are defined anyway.
    """
    if not stable_mask:
        gs.fatal(_("Option stable_mask is required for method=spline"))

    pid = os.getpid()
    stable_dod = f"tmp_rdembias_sp_dod_{pid}"
    pts = f"tmp_rdembias_sp_pts_{pid}"
    field_coarse = f"tmp_rdembias_sp_field_{pid}"
    TMP_RASTERS.extend([stable_dod, field_coarse])

    gs.mapcalc(
        f"{stable_dod} = if(!isnull({stable_mask}), {dod}, null())",
        overwrite=True,
        quiet=True,
    )
    n_avail = int(gs.parse_command("r.univar", map=stable_dod, flags="g").get("n", 0))
    if n_avail < 100:
        gs.fatal(_("Only {} stable cells available for the spline fit").format(n_avail))
    n_pts = min(int(npoints), n_avail)
    if n_pts < int(npoints):
        gs.message(
            _("Sampling all {} stable cells (requested {})").format(n_pts, npoints)
        )
    gs.run_command(
        "r.random",
        input=stable_dod,
        npoints=n_pts,
        vector=pts,
        seed=42,
        overwrite=True,
        quiet=True,
    )

    region = gs.region()
    try:
        gs.run_command("g.region", res=res, flags="a")
        gs.run_command(
            "v.surf.rst",
            input=pts,
            zcolumn="value",
            elevation=field_coarse,
            tension=tension,
            smooth=smooth,
            overwrite=True,
            quiet=True,
        )
    finally:
        gs.run_command(
            "g.region",
            n=region["n"],
            s=region["s"],
            e=region["e"],
            w=region["w"],
            nsres=region["nsres"],
            ewres=region["ewres"],
        )

    field = bias_field or f"tmp_rdembias_sp_field1_{pid}"
    if not bias_field:
        TMP_RASTERS.append(field)
    gs.run_command(
        "r.resamp.interp",
        input=field_coarse,
        output=field,
        method="bilinear",
        overwrite=gs.overwrite(),
    )
    gs.mapcalc(f"{output} = {dod} - {field}", overwrite=gs.overwrite())
    gs.run_command("g.remove", type="vector", name=pts, flags="f", quiet=True)
    gs.message(
        _(
            "Spline bias field: {} points, tension={}, smooth={}, "
            "fit at {} m, resampled bilinearly"
        ).format(n_pts, tension, smooth, res)
    )
    gs.run_command(
        "r.support",
        map=output,
        description=(
            f"spline bias: npoints={n_pts} tension={tension} "
            f"smooth={smooth} res={res} seed=42"
        ),
    )


def main():
    dod = options["dod"]
    output = options["output"]
    method = options["method"]
    predictors = options["predictors"].split(",") if options["predictors"] else []
    stable_mask = options["stable_mask"]
    mask = options["mask"]
    bias_field = options["bias_field"]
    output_se = options["output_se"]
    output_leverage = options["output_leverage"]
    log_predictors = (
        options["log_predictors"].split(",") if options["log_predictors"] else []
    )
    window = int(options["window"])
    trim_low = float(options["trim_low"])
    trim_high = float(options["trim_high"])

    if not gs.find_file(dod, element="raster")["name"]:
        gs.fatal(_("Raster map <{}> not found").format(dod))

    if method == "spline":
        if output_se or output_leverage:
            gs.warning(
                _("Options output_se/output_leverage are ignored for method=spline")
            )
        if options["fit_json"]:
            gs.warning(_("Option fit_json is ignored for method=spline"))
        correct_spline(
            dod,
            output,
            stable_mask,
            bias_field,
            float(options["spline_tension"]),
            float(options["spline_smooth"]),
            int(options["spline_npoints"]),
            float(options["spline_res"]),
        )
    elif method == "regression":
        correct_regression(
            dod,
            output,
            predictors,
            stable_mask,
            bias_field,
            output_se,
            output_leverage,
            log_predictors,
            options["fit_json"],
        )
    else:
        if output_se or output_leverage:
            gs.warning(
                _("Options output_se/output_leverage are ignored for method=forest")
            )
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
