#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.errprop
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Propagate per-source vertical uncertainty into a DEM of
#            Difference (DoD) and derive Level of Detection, t/p significance,
#            and categorical erosion/deposition significance classes.
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Propagate DEM uncertainty into a DoD and derive significance
# % keyword: raster
# % keyword: DEM
# % keyword: uncertainty
# % keyword: error propagation
# % keyword: change detection
# %end

# %option G_OPT_R_INPUT
# % key: dod
# % description: DEM of Difference raster (dem - reference)
# % required: yes
# %end

# %option G_OPT_R_INPUTS
# % key: sigma
# % description: One or more vertical uncertainty rasters, combined in quadrature
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output_sigma
# % description: Output propagated DoD uncertainty raster (sqrt of summed squares)
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output_lod
# % description: Output Level of Detection raster at the given confidence
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output_tvalue
# % description: Output t-value raster (|DoD| / sigma)
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output_pvalue
# % description: Output two-tailed p-value raster
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output_class
# % description: Output categorical significance raster (erosion/deposition classes)
# % required: no
# %end

# %option
# % key: confidence
# % type: double
# % answer: 0.95
# % options: 0.0-1.0
# % description: Confidence level for the Level of Detection
# % required: no
# %end

# %option
# % key: pmethod
# % type: string
# % answer: normal
# % options: normal,student
# % description: Distribution used for the p-value raster
# % required: no
# %end

# %option
# % key: df
# % type: integer
# % description: Degrees of freedom for the Student-t p-value (pmethod=student)
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


def z_from_confidence(confidence):
    """Two-tailed normal critical value for a confidence level."""
    from scipy.stats import norm

    return float(norm.ppf((1.0 + confidence) / 2.0))


def propagate_sigma(sigma_maps, output):
    """Combine uncertainty sources in quadrature: sqrt(sum(sigma_i^2)).

    NULL in any source propagates to NULL in the result so that the DoD
    uncertainty is only defined where every source is defined.
    """
    terms = " + ".join(f"pow({m}, 2)" for m in sigma_maps)
    not_null = " && ".join(f"!isnull({m})" for m in sigma_maps)
    expr = f"{output} = if({not_null}, sqrt({terms}), null())"
    gs.mapcalc(expr, overwrite=gs.overwrite())
    gs.run_command(
        "r.support",
        map=output,
        title="Propagated DoD uncertainty (1 sigma)",
        units="metres",
    )
    return output


def calc_lod(sigma_dod, output, confidence):
    """LoD = z(confidence) * sigma_dod."""
    z = z_from_confidence(confidence)
    gs.mapcalc(f"{output} = {z} * {sigma_dod}", overwrite=gs.overwrite())
    gs.run_command(
        "r.support",
        map=output,
        title=f"Level of Detection ({confidence * 100:.0f}% CI)",
        units="metres",
    )
    gs.message(_("LoD critical value z({:.2f}) = {:.4f}").format(confidence, z))
    return output


def calc_tvalue(dod, sigma_dod, output):
    """t = |DoD| / sigma_dod, undefined where sigma <= 0."""
    expr = (
        f"{output} = if(!isnull({sigma_dod}) && {sigma_dod} > 0, "
        f"abs({dod}) / {sigma_dod}, null())"
    )
    gs.mapcalc(expr, overwrite=gs.overwrite())
    gs.run_command("r.support", map=output, title="DoD t-value (|DoD|/sigma)")
    return output


def calc_pvalue_normal(dod, sigma_dod, output):
    """Two-tailed p-value via the Abramowitz and Stegun (26.2.17) normal-CDF
    approximation, evaluated entirely in r.mapcalc.
    """
    b1, b2, b3, b4, b5 = (
        0.319381530,
        -0.356563782,
        1.781477937,
        -1.821255978,
        1.330274429,
    )
    pi = 3.141592653589793
    pid = os.getpid()
    x = f"tmp_errprop_x_{pid}"
    phi = f"tmp_errprop_phi_{pid}"
    tt = f"tmp_errprop_tt_{pid}"
    poly = f"tmp_errprop_poly_{pid}"
    cdf = f"tmp_errprop_cdf_{pid}"
    TMP_RASTERS.extend([x, phi, tt, poly, cdf])

    gs.mapcalc(
        f"{x} = if(!isnull({sigma_dod}) && {sigma_dod} > 0, "
        f"abs({dod}) / {sigma_dod}, null())",
        overwrite=True,
        quiet=True,
    )
    gs.mapcalc(
        f"{phi} = exp(-({x}^2) / 2.0) / sqrt(2.0 * {pi})",
        overwrite=True,
        quiet=True,
    )
    gs.mapcalc(f"{tt} = 1.0 / (1.0 + 0.2316419 * {x})", overwrite=True, quiet=True)
    gs.mapcalc(
        f"{poly} = {b1}*{tt} + {b2}*pow({tt},2) + {b3}*pow({tt},3) "
        f"+ {b4}*pow({tt},4) + {b5}*pow({tt},5)",
        overwrite=True,
        quiet=True,
    )
    gs.mapcalc(f"{cdf} = 1.0 - {phi} * {poly}", overwrite=True, quiet=True)
    # Two-tailed: p = 2 * (1 - Phi(x)), clamped to [0, 1].
    gs.mapcalc(
        f"{output} = min(1.0, max(0.0, 2.0 * (1.0 - {cdf})))",
        overwrite=gs.overwrite(),
    )
    gs.run_command("r.support", map=output, title="DoD p-value (two-tailed, normal)")
    return output


def calc_pvalue_student(dod, sigma_dod, output, df):
    """Two-tailed Student-t p-value via scipy, applied through numpy arrays."""
    import numpy as np
    from grass.script import array as garray
    from scipy.stats import t as student_t

    t_map = f"tmp_errprop_t_student_{os.getpid()}"
    TMP_RASTERS.append(t_map)
    calc_tvalue(dod, sigma_dod, t_map)
    t_arr = garray.array(t_map)
    out_arr = garray.array()
    out_arr[...] = np.clip(2.0 * student_t.sf(np.asarray(t_arr), df), 0.0, 1.0)
    out_arr.write(mapname=output, overwrite=gs.overwrite())
    gs.run_command(
        "r.support",
        map=output,
        title=f"DoD p-value (two-tailed, Student-t df={df})",
    )
    return output


def calc_categorical(dod, sigma_dod, output):
    """Nine-class erosion/deposition significance map.

    Each cell is labelled by the highest confidence level (68/90/95/99%) at
    which |DoD| exceeds the corresponding LoD, signed by the DoD direction.
    """
    levels = [(0.99, 4), (0.95, 3), (0.90, 2), (0.68, 1)]
    z = {conf: z_from_confidence(conf) for conf, _code in levels}

    # Build nested if() from strongest to weakest level.
    expr = "0"
    for conf, code in reversed(levels):
        lod = f"{z[conf]} * {sigma_dod}"
        expr = f"if(abs({dod}) >= {lod}, if({dod} > 0, {code}, -{code}), {expr})"
    full = f"{output} = if(isnull({dod}) || isnull({sigma_dod}), null(), {expr})"
    gs.mapcalc(full, overwrite=gs.overwrite())

    rules = "\n".join(
        [
            "-4:Erosion >=99%",
            "-3:Erosion >=95%",
            "-2:Erosion >=90%",
            "-1:Erosion >=68%",
            "0:Not significant",
            "1:Deposition >=68%",
            "2:Deposition >=90%",
            "3:Deposition >=95%",
            "4:Deposition >=99%",
            "",
        ]
    )
    gs.write_command("r.category", map=output, rules="-", separator=":", stdin=rules)
    color_rules = "\n".join(
        [
            "-4 178:24:43",
            "-2 239:138:98",
            "-1 253:219:199",
            "0 247:247:247",
            "1 209:229:240",
            "2 103:169:207",
            "4 33:102:172",
            "",
        ]
    )
    gs.write_command("r.colors", map=output, rules="-", stdin=color_rules)
    gs.run_command(
        "r.support",
        map=output,
        units="class",
        title="DoD significance classes",
        description="Signed erosion/deposition significance at 68/90/95/99% CI",
    )
    return output


def main():
    dod = options["dod"]
    sigma_maps = options["sigma"].split(",")
    output_sigma = options["output_sigma"]
    output_lod = options["output_lod"]
    output_tvalue = options["output_tvalue"]
    output_pvalue = options["output_pvalue"]
    output_class = options["output_class"]
    confidence = float(options["confidence"])
    pmethod = options["pmethod"]
    df = options["df"]

    for name in [dod] + sigma_maps:
        if not gs.find_file(name, element="raster")["name"]:
            gs.fatal(_("Raster map <{}> not found").format(name))

    if pmethod == "student" and output_pvalue and not df:
        gs.fatal(_("Option df is required when pmethod=student"))

    propagate_sigma(sigma_maps, output_sigma)
    gs.message(_("Propagated DoD uncertainty: <{}>").format(output_sigma))

    if output_lod:
        calc_lod(output_sigma, output_lod, confidence)
    if output_tvalue:
        calc_tvalue(dod, output_sigma, output_tvalue)
    if output_pvalue:
        if pmethod == "student":
            calc_pvalue_student(dod, output_sigma, output_pvalue, int(df))
        else:
            calc_pvalue_normal(dod, output_sigma, output_pvalue)
    if output_class:
        calc_categorical(dod, output_sigma, output_class)

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
