#!/usr/bin/env python3

##############################################################################
# MODULE:    r.dem.screen
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Regional screening for topographic and spectral change.
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Regional screening: fuse topographic and spectral change
# % keyword: raster
# % keyword: change detection
# % keyword: DEM
# % keyword: NDVI
# % keyword: disaster response
# % keyword: triage
# %end

# %option G_OPT_R_INPUT
# % key: dod
# % description: DEM of Difference raster (significant change only, 10 m)
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % key: spectral_change
# % description: Spectral change raster (NDVI or VARI; negative = vegetation loss)
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output triage raster (0-3 priority classes)
# % required: yes
# %end

# %option
# % key: topo_threshold
# % type: double
# % answer: 1.0
# % description: |DoD| threshold (m) above which topographic change is flagged
# % required: no
# %end

# %option
# % key: spectral_threshold
# % type: double
# % answer: -0.15
# % description: Spectral change threshold below which vegetation loss is flagged
# % required: no
# %end

# %option G_OPT_V_INPUT
# % key: infrastructure
# % label: Infrastructure vector (roads, rail, utilities) for hazard overlay
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: hazard_output
# % description: Output hazard priority raster (requires infrastructure input)
# % required: no
# %end

# %option
# % key: infra_buffer_m
# % type: double
# % answer: 30.0
# % description: Buffer distance (m) around infrastructure for hazard intersection
# % required: no
# %end

import atexit
import sys
import os

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


def compute_triage(dod, spectral_change, output, topo_thresh, spec_thresh):
    spectral_exists = (
        spectral_change and gs.find_file(spectral_change, element="raster")["name"]
    )

    if spectral_exists:
        gs.mapcalc(
            f"{output} = "
            f"if(abs({dod}) >= {topo_thresh} && "
            f"{spectral_change} <= {spec_thresh}, 3,"
            f"if(abs({dod}) >= {topo_thresh}, 2,"
            f"if({spectral_change} <= {spec_thresh}, 1, 0)))",
            overwrite=gs.overwrite(),
        )
        gs.message(_("Triage: topographic + spectral fusion"))
    else:
        gs.mapcalc(
            f"{output} = if(abs({dod}) >= {topo_thresh}, 2, 0)",
            overwrite=gs.overwrite(),
        )
        gs.message(_("Triage: topographic change only (no spectral input)"))

    # Assign category labels
    gs.write_command(
        "r.category",
        map=output,
        separator=":",
        rules="-",
        stdin="""0:No significant change
1:Spectral change (vegetation damage)
2:Topographic change (geomorphic)
3:Topo + Spectral (highest priority)""",
    )

    # Report
    raw = gs.read_command("r.stats", input=output, flags="cn", separator=",").strip()
    gs.message("")
    gs.message(_("Triage summary:"))
    reg = gs.region()
    cell_area = reg["ewres"] * reg["nsres"]
    for row in raw.split("\n"):
        if row.strip():
            val, count = row.split(",")
            area_km2 = int(count) * cell_area / 1e6
            label = {
                "0": "No change",
                "1": "Spectral only",
                "2": "Topo change",
                "3": "Topo+Spectral",
            }.get(val, val)
            gs.message(
                _(
                    "  Class {val} ({label:25s}): {count:7,} cells  ({area:.2f} km2)"
                ).format(val=val, label=label, count=int(count), area=area_km2)
            )


def compute_hazard(
    triage,
    infrastructure,
    infra_buffer_m,
    hazard_output,
    tmp_prefix,
):
    infrastructure_exists = (
        infrastructure and gs.find_file(infrastructure, element="vector")["name"]
    )

    if not infrastructure_exists:
        gs.warning(_("No infrastructure vector found. Skipping hazard overlay."))
        return

    buf_v = f"{tmp_prefix}_infra_buf"
    buf_r = f"{tmp_prefix}_infra_buf_r"
    infra_zone = f"{tmp_prefix}_infra_zone"
    TMP_VECTORS.append(buf_v)
    TMP_RASTERS.extend([buf_r, infra_zone])

    gs.run_command(
        "v.buffer",
        input=infrastructure,
        output=buf_v,
        distance=infra_buffer_m,
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
    gs.mapcalc(f"{infra_zone} = if(isnull({buf_r}), 0, 1)", overwrite=True)

    gs.mapcalc(
        f"{hazard_output} = "
        f"if({triage} >= 2 && {infra_zone} == 1, 3,"
        f"if({triage} >= 2, 2,"
        f"if({infra_zone} == 1, 1, 0)))",
        overwrite=gs.overwrite(),
    )

    gs.write_command(
        "r.category",
        map=hazard_output,
        separator=":",
        rules="-",
        stdin="""0:No change / no infrastructure
1:Infrastructure (no change detected)
2:Change detected (no infrastructure)
3:CRITICAL - Change + Infrastructure""",
    )

    gs.message(_("Hazard overlay complete."))


def main():
    dod = options["dod"]
    spectral = options.get("spectral_change", "")
    output = options["output"]
    topo_thresh = float(options["topo_threshold"])
    spec_thresh = float(options["spectral_threshold"])
    infra = options.get("infrastructure", "")
    hazard_out = options.get("hazard_output", "")
    infra_buf = float(options["infra_buffer_m"])
    tmp_prefix = f"tmp_rdemscreen_{os.getpid()}"

    proj = gs.parse_command("g.proj", flags="g")
    units = str(proj.get("units", "")).lower()
    if proj.get("proj") in ("ll", "longlat") or "degree" in units:
        gs.warning(
            _(
                "Current CRS uses geographic (degree) units; reported areas "
                "assume a projected CRS with metric units"
            )
        )

    compute_triage(dod, spectral, output, topo_thresh, spec_thresh)

    if infra and hazard_out:
        compute_hazard(output, infra, infra_buf, hazard_out, tmp_prefix)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
