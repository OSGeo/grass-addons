#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.surf.rst.cv
# AUTHOR:       Corey T. White, NCSU GeoForAll Lab
# PURPOSE:      Cross-validation of procedures for v.surf.rst
# COPYRIGHT:    (C) 2025 OpenPlains Inc. and the GRASS Development Team
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Performs cross-validation proceedure to optimize the parameterization of v.surf.rst tension and smoothing paramters.
# % keyword: raster
# % keyword: surface
# % keyword: interpolation
# % keyword: cross-validation
# % keyword: rst
# % keyword: json
# %end

# %option G_OPT_V_INPUT
# % key: point_cloud
# % label: Name of the input point cloud vector map
# % description: Name of the input point cloud vector map
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_R_INPUT
# % key: mask
# % label: Mask raster map
# % type: string
# % required: no
# % description: Name of the mask raster map
# %end

# %option
# % key: tension
# % type: integer
# % required: no
# % description: Tension parameter for cross-validation (default: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120])
# % multiple: yes
# %end

# %option
# % key: smooth
# % type: double
# % required: no
# % description: Smoothing parameter for cross-validation (default: [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
# % multiple: yes
# %end

# %option
# % key: cv_prefix
# % label: Prefix to use for cross-validation output maps (must be used with -s)
# % type: string
# % required: no
# % description: Prefix to use for cross-validation output maps
# % guisection: Output
# %end

# %option G_OPT_M_NPROCS
# %end

# %flag
# % key: s
# % description: Save cross-validation outputs
# %end

from __future__ import annotations
import sys
import atexit
import uuid
import math
import grass.script as gs
import grass.script.core as gcore
from grass.exceptions import CalledModuleError

tmp_raster_list = []


def cleanup():
    """ "Remove temporary raster maps"""
    if len(tmp_raster_list) > 0:
        gs.run_command(
            "g.remove",
            type="raster",
            name=",".join(tmp_raster_list),
            # pattern="tmp_*",
            flags="f",
            quiet=True,
        )


def check_addon_installed(addon: str, fatal=True) -> None:
    """Check if a GRASS GIS addon is installed"""
    if not gcore.find_program(addon, "--help"):
        call = gcore.fatal if fatal else gcore.warning
        call(
            _(
                "Addon {a} is not installed. Please install it using g.extension."
            ).format(a=addon)
        )


def set_cv_colors(hand: str) -> None:
    """Set HAND raster colors based on Norbre et al. 2011"""
    hand_colors = """
        0 white
        5 #1d91c0
        15 #41ab5d
        100% #ec7014
        nv white
        default grey
    """
    try:
        gs.write_command("r.colors", map=hand, rules="-", stdin=hand_colors, quiet=True)
    except CalledModuleError as e:
        gs.fatal(_("Error setting HAND colors: %s") % e.stderr)


def generate_temp_raster_name(raster_name: str) -> str:
    """Generate a temporary raster name"""
    uuid_str = str(uuid.uuid4())
    tmp_raster_name = f"tmp_{raster_name}_{uuid_str}"
    gs.debug(_("Temporary raster name: %s") % tmp_raster_name)
    tmp_raster_list.append(tmp_raster_name)
    return tmp_raster_name


def check_raster_exists(raster: str) -> str:
    # check if input file exists
    if not gs.find_file(raster)["file"]:
        gs.fatal(_("Raster map %s not found") % raster)
    return raster


def cross_validate(point_cloud: str, **kwargs) -> list[str]:
    """Cross-validate v.surf.rst parameters"""
    base_output = "cvdev"

    # Set tension
    tension = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120]
    if kwargs.get("tension"):
        tension = ",".join(kwargs.get("tension"))

    # Set smoothing
    smoothing = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    if kwargs.get("smooth"):
        smoothing = ",".join(kwargs.get("smooth"))

    output_list = []
    for t in tension:
        for s in smoothing:
            output_name = f"{base_output}_{t}_{str(s).replace('.', '')}"
            gs.run_command(
                "v.surf.rst",
                input=point_cloud,
                cvdev=output_name,
                mask=kwargs.get("mask"),
                smooth=s,
                tension=t,
                npmin=100,
                nprocs=kwargs.get("nprocs"),
                flags="c",
            )
            output_list.append(output_name)
    return output_list


def extract_residuals(cvdev_map: str) -> tuple[float, float]:
    # Extract residuals from the cvdev map
    residuals = gs.parse_command("v.db.select", map=cvdev_map, format="json")

    residuals = [float(res["flt1"]) for res in residuals["records"] if res]

    # # Calculate RMSE and MAE
    n = len(residuals)
    mse = sum([res**2 for res in residuals]) / n
    rmse = math.sqrt(mse)
    mae = sum([abs(res) for res in residuals]) / n
    # return residuals
    return (rmse, mae)


def cvdev_results(cvdev_list: list[str]):
    results_list = []
    for cvdev in cvdev_list:
        rmse, mae = extract_residuals(cvdev)
        base, tension, smooth = cvdev.split("_")
        results_list.append(
            {"tension": tension, "smooth": smooth, "rmse": rmse, "mae": mae}
        )

    return results_list


def main():
    # Required options
    point_cloud = options["point_cloud"]
    mask = options.get("mask")
    tension_list = options["tension"]
    smoothing_list = options["smooth"]
    nprocs = options["nprocs"]

    # Run cross-validation
    cv_map_list = cross_validate(
        point_cloud,
        smooth=smoothing_list,
        tension=tension_list,
        mask=mask,
        nprocs=nprocs,
    )
    results_list = cvdev_results(cv_map_list)
    best_combination = min(results_list, key=lambda x: x["rmse"])

    gs.message(_("Best Parameter Combination:"))
    gs.message(
        _("Tension: %s, Smoothing: %s, RMSE: %d, MAE: %d")
        % best_combination["tension"],
        best_combination["smooth"],
        rmse=best_combination["rmse"],
        mae=best_combination["mae"],
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
