#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.surf.rst.cv
# AUTHOR:       Corey T. White, NCSU GeoForAll Lab
# PURPOSE:      Cross-validation of procedures for optimizing regularized spline
#               with tension interpolation (RST) smoothing and tension parameters
#               for use with v.surf.rst.
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
# % guisection: Input
# %end

# %option
# % key: tension
# % type: integer
# % required: no
# % description: Tension parameter for cross-validation
# % multiple: yes
# % answer: 10, 20, 40, 60, 80, 100
# % guisection: Cross-Validation
# %end

# %option
# % key: smooth
# % type: double
# % required: no
# % description: Smoothing parameter for cross-validation
# % multiple: yes
# % answer: 0.01, 0.1, 0.5, 1.0, 5.0, 10.0
# % guisection: Cross-Validation
# %end

# %option G_OPT_V_FIELD
# % key: layer
# % guisection: RST Parameters
# % required: no
# %end

# %option G_OPT_DB_COLUMN
# % key: zcolumn
# % label: Name of the attribute column with values to be used for approximation
# % description: If not given and input is 2D vector map then category values are used. If input is 3D vector map then z-coordinates are used.
# % required: no
# % guisection: RST Parameters
# %end

# %option G_OPT_DB_WHERE
# % key: where
# % label: WHERE conditions of SQL statement without 'where' keyword
# % description: Example: elevation < 500 and elevation >= 1
# % required: no
# % guisection: RST Parameters
# %end

# %option
# % key: segmax
# % type: integer
# % required: no
# % description: Maximum number of points in segment
# % answer: 40
# % guisection: RST Parameters
# %end

# %option
# % key: dmin
# % type: double
# % required: no
# % description: Minimum distance between points
# % answer: 0.0
# % guisection: RST Parameters
# %end

# %option
# % key: dmax
# % type: double
# % required: no
# % description: Maximum distance between points on isoline (to insert additional points)
# % answer: 0.0
# % guisection: RST Parameters
# %end

# %option
# % key: zscale
# % type: double
# % required: no
# % description: Conversion factor for values used for approximation
# % answer: 1.0
# % guisection: RST Parameters
# %end

# %option
# % key: theta
# % type: double
# % required: no
# % description: Anisotropy angle (in degrees counterclockwise from East)
# %end

# %option
# % key: scalex
# % type: double
# % required: no
# % description: Anisotropy scaling factor
# %end

# %option
# % key: cv_prefix
# % label: Prefix to use for cross-validation output maps
# % type: string
# % required: no
# % description: Prefix to use for cross-validation output cross-validation errors vector point map. Value must be set to save the cross-validation errors to a vector maps.
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

from __future__ import annotations

import sys
import atexit
from typing import TYPE_CHECKING
import uuid
import math
import json
from pathlib import Path

if TYPE_CHECKING:
    from optparse import Option

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


def set_tension_parameter(tension_option: Option[str]) -> list[int]:
    """Set tension parameter"""
    tension = DEFAULT_TENSION
    if tension_option:
        tension = tension_option.split(",")
    gs.message(_("Tension values: %s") % tension)
    return tension


def set_smoothing_parameter(smoothing_option: Option[str]) -> list[float]:
    """Set smoothing parameter"""
    smoothing = DEFAULT_SMOOTHING
    if smoothing_option:
        smoothing = smoothing_option.split(",")
    gs.message(_("Smoothing values: %s") % smoothing)
    return smoothing


def set_cvdev_parameter(cv_prefix: Option[str]) -> str:
    """Set the cvdev parameter"""
    CVDEV_PREFIX = "cvdev"
    if cv_prefix:
        cvdev = cv_prefix
    else:
        cvdev = generate_temp_raster_name(CVDEV_PREFIX)
    return cvdev


def cross_validate(
    point_cloud: str,
    tension_list: list[int],
    smoothing_list: list[float],
    cv_prefix: str,
    **kwargs: dict,
) -> list[str]:
    """Cross-validate v.surf.rst parameters"""
    gs.message(_("Starting cross-validation..."))

    output_list = []
    for t in tension_list:
        for s in smoothing_list:
            output_name = f"{cv_prefix}_{t}_{str(s).replace('.', '')}"
            try:
                gs.run_command(
                    "v.surf.rst",
                    **kwargs,
                    input=point_cloud,
                    cvdev=output_name,
                    smooth=s,
                    tension=t,
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

    # Calculate RMSE and MAE
    n = len(residuals)
    mse = sum([res**2 for res in residuals]) / n
    rmse = math.sqrt(mse)
    mae = sum([abs(res) for res in residuals]) / n
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


def report_results(results_list: list[dict], format: str) -> None:
    """Report the results of the cross-validation"""
    gs.message(_("Cross-validation results:"))
    if format == "json":
        json_results = json.dumps(results_list, indent=4)
        gs.message(_(json_results))
        return json_results
    else:
        header = "Tension, Smoothing, RMSE, MAE"
        gs.message(_(header))
        for res in results_list:
            gs.message(
                _("%s, %s, %f, %f")
                % (res["tension"], res["smooth"], res["rmse"], res["mae"])
            )

        csv_results = "\n".join(
            [",".join([str(res[k]) for k in res]) for res in results_list]
        )
        csv_results = f"{header}\n{csv_results}"
        return csv_results


def main():
    # Required options
    point_cloud = options["point_cloud"]

    # Output options
    output_file = options.get("output_file")
    format = options["format"]

    # Set parameters
    cvdev = set_cvdev_parameter(options.get("cv_prefix"))
    tension = set_tension_parameter(options.get("tension"))
    smoothing = set_smoothing_parameter(options.get("smooth"))

    # Run cross-validation
    cv_map_list = cross_validate(
        point_cloud,
        tension_list=tension,
        smoothing_list=smoothing,
        cv_prefix=cvdev,
        **options,  # Pass the options to the cross-validation function kwargs
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

    results = report_results(results_list, format)
    write_output_file(results, output_file)
    return results


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
