#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.stats
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Compute terrain surface metrics from a DEM (or DoD) for use as
#            predictors in DoD uncertainty and bias modelling.
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Compute terrain surface metrics used as DoD predictors
# % keyword: raster
# % keyword: DEM
# % keyword: terrain
# % keyword: statistics
# % keyword: geomorphology
# %end

# %option G_OPT_R_INPUT
# % key: input
# % description: Input DEM (or DoD raster for metric=error_sigma_local)
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output surface-metric raster
# % required: yes
# %end

# %option
# % key: metric
# % type: string
# % required: yes
# % options: slope,roughness_std,diversity_geomorphon,diversity_shannon,error_sigma_local
# % description: Surface metric to compute
# %end

# %option
# % key: window
# % type: integer
# % answer: 7
# % description: Moving window size in cells (odd integer >= 3)
# % required: no
# %end

# %option
# % key: log_base
# % type: string
# % answer: e
# % options: e,2,10
# % description: Logarithm base for Shannon diversity
# % required: no
# %end

# %option
# % key: slope_format
# % type: string
# % answer: degrees
# % options: degrees,radians
# % description: Output format for slope
# % required: no
# %end

# %flag
# % key: e
# % description: Also compute Shannon evenness (metric=diversity_shannon)
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


def gaussian_weighting_factor(window):
    """Match the focal Gaussian falloff used across the DoD workflow."""
    radius = (float(window) - 1.0) * 0.5
    return radius * 0.5


def log_expr(p, log_base):
    if log_base == "e":
        return f"log({p})"
    if log_base == "10":
        return f"log10({p})"
    return f"log({p}) / log(2)"


def metric_slope(input_raster, output, slope_format):
    gs.run_command(
        "r.slope.aspect",
        elevation=input_raster,
        slope=output,
        format=slope_format,
        overwrite=gs.overwrite(),
    )


def metric_roughness_std(input_raster, output, window):
    wf = gaussian_weighting_factor(window)
    gs.run_command(
        "r.neighbors",
        input=input_raster,
        output=output,
        method="stddev",
        size=window,
        weighting_factor=wf,
        weighting_function="gaussian",
        overwrite=gs.overwrite(),
    )


def metric_diversity_geomorphon(input_raster, output, window):
    landforms = f"tmp_rdemstats_forms_{os.getpid()}"
    TMP_RASTERS.append(landforms)
    gs.run_command(
        "r.geomorphon",
        elevation=input_raster,
        forms=landforms,
        search=7,
        flat=4,
        overwrite=True,
        quiet=True,
    )
    wf = gaussian_weighting_factor(window)
    gs.run_command(
        "r.neighbors",
        input=landforms,
        output=output,
        method="diversity",
        size=window,
        weighting_factor=wf,
        weighting_function="gaussian",
        overwrite=gs.overwrite(),
    )


def metric_diversity_shannon(forms, output, window, log_base, evenness):
    """Local Shannon diversity H' = -sum(p * log(p)) over category proportions
    in a moving window, computed from a categorical input (e.g. geomorphons).
    """
    cats_txt = gs.read_command("r.stats", flags="nc", input=forms)
    cats = [
        int(float(line.split()[0]))
        for line in cats_txt.strip().splitlines()
        if line.strip()
    ]
    if not cats:
        gs.fatal(_("No categories found in <{}> for Shannon diversity").format(forms))

    p_maps = []
    for c in cats:
        indicator = f"tmp_rdemstats_I_{c}_{os.getpid()}"
        proportion = f"tmp_rdemstats_p_{c}_{os.getpid()}"
        TMP_RASTERS.extend([indicator, proportion])
        gs.mapcalc(
            f"{indicator} = if({forms} == {c}, 1, 0)",
            overwrite=True,
            quiet=True,
        )
        gs.run_command(
            "r.neighbors",
            input=indicator,
            output=proportion,
            method="average",
            size=window,
            overwrite=True,
            quiet=True,
        )
        p_maps.append(proportion)

    terms = [f"if({p} > 0, -{p} * {log_expr(p, log_base)}, 0)" for p in p_maps]
    gs.mapcalc(f"{output} = " + " + ".join(terms), overwrite=gs.overwrite())

    if evenness:
        evenness_map = f"{output}_evenness"
        if gs.find_file(evenness_map, element="raster")["name"] and not gs.overwrite():
            gs.fatal(
                _("Raster map <{}> already exists. Use --overwrite.").format(
                    evenness_map
                )
            )
        rich = f"tmp_rdemstats_rich_{os.getpid()}"
        TMP_RASTERS.append(rich)
        gs.run_command(
            "r.neighbors",
            input=forms,
            output=rich,
            method="diversity",
            size=window,
            overwrite=True,
            quiet=True,
        )
        denom = log_expr(rich, log_base)
        gs.mapcalc(
            f"{evenness_map} = if({rich} > 1, {output} / ({denom}), null())",
            overwrite=gs.overwrite(),
        )


def metric_error_sigma_local(input_raster, output, window):
    """Robust local standard deviation via MAD:
    sigma ~= 1.4826 * median(|x - median(x)|) in a moving window.
    """
    pid = os.getpid()
    in_f = f"tmp_rdemstats_f_{pid}"
    median_r = f"tmp_rdemstats_med_{pid}"
    absdev_r = f"tmp_rdemstats_absdev_{pid}"
    mad_r = f"tmp_rdemstats_mad_{pid}"
    TMP_RASTERS.extend([in_f, median_r, absdev_r, mad_r])
    wf = gaussian_weighting_factor(window)

    gs.mapcalc(f"{in_f} = float({input_raster})", overwrite=True, quiet=True)
    gs.run_command(
        "r.neighbors",
        input=in_f,
        output=median_r,
        method="median",
        size=window,
        weighting_factor=wf,
        weighting_function="gaussian",
        overwrite=True,
        quiet=True,
    )
    gs.mapcalc(f"{absdev_r} = abs({in_f} - {median_r})", overwrite=True, quiet=True)
    gs.run_command(
        "r.neighbors",
        input=absdev_r,
        output=mad_r,
        method="median",
        size=window,
        weighting_factor=wf,
        weighting_function="gaussian",
        overwrite=True,
        quiet=True,
    )
    gs.mapcalc(f"{output} = 1.4826 * {mad_r}", overwrite=gs.overwrite())


def main():
    input_raster = options["input"]
    output = options["output"]
    metric = options["metric"]
    window = int(options["window"])
    log_base = options["log_base"]
    slope_format = options["slope_format"]
    evenness = flags["e"]

    if not gs.find_file(input_raster, element="raster")["name"]:
        gs.fatal(_("Raster map <{}> not found").format(input_raster))
    if window < 3 or window % 2 == 0:
        gs.fatal(_("Option window must be an odd integer >= 3"))

    if metric == "slope":
        metric_slope(input_raster, output, slope_format)
    elif metric == "roughness_std":
        metric_roughness_std(input_raster, output, window)
    elif metric == "diversity_geomorphon":
        metric_diversity_geomorphon(input_raster, output, window)
    elif metric == "diversity_shannon":
        metric_diversity_shannon(input_raster, output, window, log_base, evenness)
    elif metric == "error_sigma_local":
        metric_error_sigma_local(input_raster, output, window)

    gs.run_command(
        "r.support", map=output, title=f"r.dem.stats {metric} (window={window})"
    )
    gs.message(_("Surface metric <{}> written: {}").format(metric, output))
    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
