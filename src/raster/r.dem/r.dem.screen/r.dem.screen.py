#!/usr/bin/env python3
# pyright: reportMissingImports=false

##############################################################################
# MODULE:    r.dem.screen
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Regional screening for topographic and spectral change.
#
# COPYRIGHT: (C) 2025 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
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
# % description: Spectral change raster
# % description: (NDVI or VARI; negative = vegetation loss)
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output triage raster (0–3 priority classes)
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
# % description: Infrastructure vector (roads, rail, utilities) for hazard overlay
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

import sys
import os

import grass.script as gs


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
            overwrite=True,
        )
        gs.message("Triage: topographic + spectral fusion")
    else:
        gs.mapcalc(f"{output} = if(abs({dod}) >= {topo_thresh}, 2, 0)", overwrite=True)
        gs.message("Triage: topographic change only (no spectral input)")

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
    gs.message("\nTriage summary:")
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
                f"  Class {val} ({label:25s}): {int(count):7,} cells  "
                f"({area_km2:.2f} km²)"
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
        gs.warning("No infrastructure vector found. Skipping hazard overlay.")
        return

    buf_v = f"{tmp_prefix}_infra_buf"
    buf_r = f"{tmp_prefix}_infra_buf_r"

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
    gs.mapcalc(f"_infra_zone = if(isnull({buf_r}), 0, 1)", overwrite=True)

    gs.mapcalc(
        f"{hazard_output} = "
        f"if({triage} >= 2 && _infra_zone == 1, 3,"
        f"if({triage} >= 2, 2,"
        f"if(_infra_zone == 1, 1, 0)))",
        overwrite=True,
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

    gs.message("Hazard overlay complete.")
    gs.run_command(
        "g.remove",
        type="raster,vector",
        name=f"{buf_v},{buf_r},_infra_zone",
        flags="f",
        quiet=True,
    )


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

    compute_triage(dod, spectral, output, topo_thresh, spec_thresh)

    if infra and hazard_out:
        compute_hazard(output, infra, infra_buf, hazard_out, tmp_prefix)

    gs.run_command(
        "g.remove", type="raster", pattern=f"{tmp_prefix}*", flags="f", quiet=True
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
