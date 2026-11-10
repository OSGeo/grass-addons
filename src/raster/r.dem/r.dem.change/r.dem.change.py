#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.change
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Compute a DEM of Difference (DoD), optionally clean it, apply a
#            Level of Detection threshold, and summarize volumetric change.
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: DoD computation with cleanup, LoD masking, and volumetric summary
# % keyword: raster
# % keyword: DEM
# % keyword: change detection
# % keyword: volume
# % keyword: geomorphology
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

# %option G_OPT_R_INPUT
# % key: lod
# % description: Level of Detection raster (from r.dem.lod or r.dem.errprop)
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output_dod
# % description: Raw DoD (dem - reference, no LoD masking); dem+reference path only
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output_sig
# % description: Significant DoD (cells where |dh| > LoD)
# % required: yes
# %end

# %option G_OPT_F_OUTPUT
# % key: volume_csv
# % description: CSV output with erosion/deposition/net volumes
# % required: no
# %end

# %option
# % key: trim_percentile
# % type: double
# % options: 0-100
# % description: Trim |DoD| blunders above this percentile before thresholding
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: stable_mask
# % description: Stable-terrain mask used to estimate the trim_percentile threshold (only used with trim_percentile)
# % required: no
# %end

# %flag
# % key: n
# % description: Remove isolated significant cells (speckle) from the significant DoD
# %end

# %flag
# % key: k
# % description: Report DoD distribution kurtosis (Fisher and Pearson)
# %end

# %rules
# % required: dod, dem
# % exclusive: dod, dem
# % exclusive: dod, output_dod
# % requires_all: dem, reference, output_dod
# % requires: reference, dem
# % requires: stable_mask, trim_percentile
# %end

import atexit
import csv
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


def trim_blunders(dod, percentile, stable_mask, output):
    """Null out gross |DoD| blunders above a percentile of the absolute
    difference. The threshold is estimated over the stable mask when one is
    supplied, otherwise over the whole DoD.
    """
    abs_dod = f"tmp_rdchange_absdod_{os.getpid()}"
    TMP_RASTERS.append(abs_dod)
    gs.mapcalc(f"{abs_dod} = abs({dod})", overwrite=True, quiet=True)

    if stable_mask:
        with gs.MaskManager(stable_mask):
            stats = gs.parse_command(
                "r.univar",
                map=abs_dod,
                percentile=percentile,
                flags="e",
                format="json",
            )
    else:
        stats = gs.parse_command(
            "r.univar",
            map=abs_dod,
            percentile=percentile,
            flags="e",
            format="json",
        )
    threshold = float(stats["percentiles"][0]["value"])
    gs.message(
        _("Trimming |DoD| blunders above the {:.1f}th percentile = {:.4f}").format(
            percentile, threshold
        )
    )
    gs.mapcalc(
        f"{output} = if(abs({dod}) <= {threshold}, {dod}, null())",
        overwrite=True,
        quiet=True,
    )
    return output


def remove_speckle(sig, output):
    """Drop isolated significant cells: keep a significant cell only when at
    least one of its eight neighbours is also significant.
    """
    neighbors = [
        f"!isnull({sig}[1,0])",
        f"!isnull({sig}[-1,0])",
        f"!isnull({sig}[0,1])",
        f"!isnull({sig}[0,-1])",
        f"!isnull({sig}[1,1])",
        f"!isnull({sig}[1,-1])",
        f"!isnull({sig}[-1,1])",
        f"!isnull({sig}[-1,-1])",
    ]
    neighbor_sum = " + ".join(neighbors)
    gs.mapcalc(
        f"{output} = if(isnull({sig}), null(), "
        f"if(({neighbor_sum}) > 0, {sig}, null()))",
        overwrite=gs.overwrite(),
        quiet=True,
    )
    return output


def report_kurtosis(dod):
    """Report Fisher and Pearson kurtosis of the DoD distribution."""
    import numpy as np
    from grass.script import array as garray
    from scipy.stats import kurtosis

    data = np.asarray(garray.array(dod)).flatten()
    data = data[np.isfinite(data)]
    if data.size == 0:
        gs.warning(_("DoD has no valid cells for kurtosis"))
        return
    fisher = float(kurtosis(data, fisher=True))
    pearson = float(kurtosis(data, fisher=False))
    gs.message(_("DoD kurtosis (Fisher):  {:.4f}").format(fisher))
    gs.message(_("DoD kurtosis (Pearson): {:.4f}").format(pearson))


def main():
    dem = options["dem"]
    reference = options["reference"]
    dod = options["dod"]
    lod = options["lod"]
    out_dod = options["output_dod"]
    out_sig = options["output_sig"]
    vol_csv = options["volume_csv"]
    trim_percentile = options["trim_percentile"]
    stable_mask = options["stable_mask"]
    denoise = flags["n"]
    want_kurtosis = flags["k"]

    inputs = [dod, lod] if dod else [dem, reference, lod]
    for name in inputs:
        if not gs.find_file(name, element="raster")["name"]:
            gs.fatal(_("Raster map <{}> not found").format(name))

    if dod:
        # Precomputed (typically bias-corrected) difference: analyze as-is.
        out_dod = dod
    else:
        # Raw DoD (always the unmodified difference).
        gs.mapcalc(f"{out_dod} = {dem} - {reference}", overwrite=gs.overwrite())

    if want_kurtosis:
        report_kurtosis(out_dod)

    # The difference that feeds significance, optionally blunder-trimmed.
    work_dod = out_dod
    if trim_percentile:
        work_dod = f"tmp_rdchange_trimmed_{os.getpid()}"
        TMP_RASTERS.append(work_dod)
        trim_blunders(out_dod, float(trim_percentile), stable_mask, work_dod)

    # Significant DoD: cells where |dh| exceeds the LoD. With -n, write the
    # raw significant cells to a temporary map and despeckle into the output.
    sig_expr = f"if(abs({work_dod}) > {lod}, {work_dod}, null())"
    if denoise:
        raw_sig = f"tmp_rdchange_sig_{os.getpid()}"
        TMP_RASTERS.append(raw_sig)
        gs.mapcalc(f"{raw_sig} = {sig_expr}", overwrite=True, quiet=True)
        remove_speckle(raw_sig, out_sig)
        gs.message(_("Removed isolated significant cells (speckle)"))
    else:
        gs.mapcalc(f"{out_sig} = {sig_expr}", overwrite=gs.overwrite())

    # Volumetric summary.
    proj = gs.parse_command("g.proj", flags="g")
    units = str(proj.get("units", "")).lower()
    if proj.get("proj") in ("ll", "longlat") or "degree" in units:
        gs.warning(
            _(
                "Current CRS uses geographic (degree) units; reported volumes "
                "assume a projected CRS with metric units"
            )
        )
    reg = gs.region()
    cell_area = reg["ewres"] * reg["nsres"]

    def _component_volume(mask_expr):
        tmp = f"tmp_rdchange_{os.getpid()}_vol"
        gs.mapcalc(f"{tmp} = {mask_expr}", overwrite=True, quiet=True)
        stats = gs.parse_command("r.univar", map=tmp, format="json")
        n_cells = int(stats.get("n") or 0)
        sum_value = float(stats["sum"]) if stats.get("sum") is not None else 0.0
        gs.run_command("g.remove", type="raster", name=tmp, flags="f", quiet=True)
        return n_cells, sum_value * cell_area

    n_dep, vol_dep = _component_volume(f"if({out_sig} > 0, {out_sig}, null())")
    n_ero, vol_ero = _component_volume(f"if({out_sig} < 0, abs({out_sig}), null())")
    n_tot = n_dep + n_ero
    vol_net = vol_dep - vol_ero

    gs.message(_("Volumetric summary (significant cells only):"))
    gs.message(_("  Deposition: {:>14,.1f} m3  ({:,} cells)").format(vol_dep, n_dep))
    gs.message(_("  Erosion:    {:>14,.1f} m3  ({:,} cells)").format(vol_ero, n_ero))
    gs.message(_("  Net:        {:>14,.1f} m3").format(vol_net))
    gs.message(_("  Net (yd3):  {:>14,.1f}").format(vol_net * 1.308))

    if vol_csv:
        with open(vol_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value_m3", "value_yd3", "n_cells", "input"])
            writer.writerow(["deposition", vol_dep, vol_dep * 1.308, n_dep, out_dod])
            writer.writerow(["erosion", vol_ero, vol_ero * 1.308, n_ero, out_dod])
            writer.writerow(["net", vol_net, vol_net * 1.308, n_tot, out_dod])
        gs.message(_("Volume stats: {}").format(vol_csv))

    gs.run_command(
        "r.support",
        map=out_sig,
        title="Significant DoD (LoD-masked)",
        description=(
            f"Erosion={vol_ero:.1f}m3  Deposition={vol_dep:.1f}m3  Net={vol_net:.1f}m3"
        ),
    )
    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
