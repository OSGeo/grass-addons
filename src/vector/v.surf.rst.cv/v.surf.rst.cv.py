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
# % description: Tension parameter for cross-validation (default: [10, 20, 40, 60, 80, 100])
# % multiple: yes
# %end

# %option
# % key: smooth
# % type: double
# % required: no
# % description: Smoothing parameter for cross-validation (default: [0.01, 0.1, 0.5, 1.0, 5.0, 10.0])
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

# %option G_OPT_F_OUTPUT
# % key: output_file
# % label: Output file
# % description: Output file for the results (default: None) json or csv
# % required: no
# % guisection: Output
# %end

# %option G_OPT_F_FORMAT
# % key: format
# % label: Output format
# % options: json,text
# % required: no
# % description: Output format for the results
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
import json
from pathlib import Path

import grass.script as gs
import grass.script.core as gcore
from grass.exceptions import CalledModuleError

tmp_layer_list = []
DEFAULT_TENSION = [10, 20, 40, 60, 80, 100]
DEFAULT_SMOOTHING = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0]


def cleanup():
    """ "Remove temporary vector maps"""
    if len(tmp_layer_list) > 0:
        gs.run_command(
            "g.remove",
            type="vector",
            name=",".join(tmp_layer_list),
            # pattern="tmp_*",
            flags="f",
            quiet=True,
        )


def generate_temp_raster_name(raster_name: str) -> str:
    """Generate a temporary raster name"""
    uuid_str = str(uuid.uuid4()).replace("-", "_")
    tmp_raster_name = f"tmp_{raster_name}_{uuid_str}"
    gs.debug(_("Temporary raster name: %s") % tmp_raster_name)
    tmp_layer_list.append(tmp_raster_name)
    return tmp_raster_name


def check_raster_exists(raster: str) -> str:
    # check if input file exists
    if not gs.find_file(raster)["file"]:
        gs.fatal(_("Raster map %s not found") % raster)
    return raster


def cross_validate(point_cloud: str, **kwargs) -> list[str]:
    """Cross-validate v.surf.rst parameters"""
    gs.message(_("Starting cross-validation..."))
    cvdev = "cvdev"
    if kwargs.get("cv_prefix"):
        cvdev = kwargs.get("cv_prefix")
    else:
        cvdev = generate_temp_raster_name(cvdev)

    # Set tension
    tension = DEFAULT_TENSION
    if kwargs.get("tension"):
        tension = kwargs.get("tension").split(",")
    gs.message(_("Tension values: %s") % tension)

    # Set smoothing
    smoothing = DEFAULT_SMOOTHING
    if kwargs.get("smooth"):
        smoothing = kwargs.get("smooth").split(",")
    gs.message(_("Smoothing values: %s") % smoothing)

    output_list = []
    for t in tension:
        for s in smoothing:
            output_name = f"{cvdev}_{t}_{str(s).replace('.', '')}"
            try:
                gs.run_command(
                    "v.surf.rst",
                    input=point_cloud,
                    cvdev=output_name,
                    mask=kwargs.get("mask", None),
                    smooth=s,
                    tension=t,
                    npmin=200,
                    nprocs=kwargs.get("nprocs", 1),
                    flags="c",
                    quiet=True,
                )
            except CalledModuleError as e:
                gs.warning(_("Error running v.surf.rst: %s") % e.stderr)

            output_list.append([output_name, t, s])

    return output_list


def extract_residuals(cvdev_map: str) -> tuple[float, float]:
    # Extract residuals from the cvdev map
    residuals = gs.parse_command(
        "v.db.select", map=cvdev_map, format="json", quiet=True
    )

    residuals = [float(res["flt1"]) for res in residuals["records"] if res]

    # # Calculate RMSE and MAE
    n = len(residuals)
    mse = sum([res**2 for res in residuals]) / n
    rmse = math.sqrt(mse)
    mae = sum([abs(res) for res in residuals]) / n
    # return residuals
    return (rmse, mae)


def cvdev_results(cvdev_list: list[str]) -> list[dict]:
    """Extract RMSE and MAE from cross-validation results"""
    results_list = []
    for cvdev, tension, smooth in cvdev_list:
        rmse, mae = extract_residuals(cvdev)
        results_list.append(
            {"tension": tension, "smooth": smooth, "rmse": rmse, "mae": mae}
        )

    return results_list


def write_output_file(results: str, output_file: str) -> None:
    if output_file:
        try:
            Path(output_file).write_text(results)
        except Exception as e:
            gs.fatal(_("Error writing output file: %s") % e)
        gs.message(_("Results written to %s") % output_file)


def report_results(results_list: list[dict], format: str, output_file: str) -> None:
    """Report the results of the cross-validation"""
    if format == "json":
        json_results = json.dumps(results_list, indent=4)
        write_output_file(json_results, output_file)
        return json_results
    else:
        gs.message(_("Cross-validation results:"))
        gs.message(_("Tension, Smoothing, RMSE, MAE"))
        for res in results_list:
            gs.message(
                _("%s, %s, %f, %f")
                % (res["tension"], res["smooth"], res["rmse"], res["mae"])
            )
        header = "Tension, Smoothing, RMSE, MAE"
        csv_results = "\n".join(
            [",".join([str(res[k]) for k in res]) for res in results_list]
        )
        csv_results = f"{header}\n{csv_results}"
        write_output_file(csv_results, output_file)


def main():
    # Required options
    point_cloud = options["point_cloud"]

    # Optional options
    mask = options.get("mask")
    tension_list = options["tension"]
    smoothing_list = options["smooth"]

    # Output options
    cv_prefix = options.get("cv_prefix")
    output_file = options.get("output_file")
    format = options["format"]

    # Processing Options
    nprocs = options["nprocs"]

    # Run cross-validation
    cv_map_list = cross_validate(
        point_cloud,
        smooth=smoothing_list,
        tension=tension_list,
        cv_prefix=cv_prefix,
        mask=mask,
        nprocs=nprocs,
    )
    results_list = cvdev_results(cv_map_list)
    best_combination = min(results_list, key=lambda x: x["rmse"])

    gs.message(_("\nBest Parameter Combination:"))
    gs.message(_("-" * 50))
    gs.message(
        _("Tension: %s, Smoothing: %s, RMSE: %f, MAE: %f")
        % (
            best_combination["tension"],
            best_combination["smooth"],
            best_combination["rmse"],
            best_combination["mae"],
        )
    )
    gs.message(_("-" * 50))

    report_results(results_list, format, output_file)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
