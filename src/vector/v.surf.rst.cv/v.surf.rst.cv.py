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
# % answer: 10,20,40,60,80,100
# % guisection: Cross-Validation
# %end

# %option
# % key: smooth
# % type: double
# % required: no
# % description: Smoothing parameter for cross-validation
# % multiple: yes
# % answer: 0.01,0.1,0.5,1.0,5.0,10.0
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
# % description: Minimum distance between points (to remove almost identical points). Default value is half of the smaller resolution of the current region.
# % guisection: RST Parameters
# %end

# %option
# % key: dmax
# % type: double
# % required: no
# % description: Maximum distance between points on isoline (to insert additional points)
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
from grass.exceptions import CalledModuleError

TMP_LAYER_LIST = []
DEFAULT_TENSION = [10, 20, 40, 60, 80, 100]
DEFAULT_SMOOTHING = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0]


def cleanup():
    """ "Remove temporary vector maps"""
    if len(TMP_LAYER_LIST) > 0:
        gs.message(_("Cleaning up temporary vector maps..."))
        tmp_layer_root = TMP_LAYER_LIST[0]
        gs.debug(_("Temporary vector maps root: %s") % tmp_layer_root)
        gs.run_command(
            "g.remove",
            type="vector",
            pattern=f"{tmp_layer_root}*",
            flags="f",
            quiet=True,
        )


def generate_tmp_layer_name(layer_name: str) -> str:
    """Generate a temporary layer name"""
    uuid_str = str(uuid.uuid4()).replace("-", "_")
    tmp_layer_name = f"tmp_{layer_name}_{uuid_str}"
    gs.debug(_("Temporary layer name: %s") % tmp_layer_name)
    TMP_LAYER_LIST.append(tmp_layer_name)
    return tmp_layer_name


def set_default_parameters(
    user_options: str, default_option: list[int | float]
) -> list[int | float]:
    """Set default parameters"""
    options = default_option
    if user_options:
        options = user_options.replace(" ", "").split(",")
    gs.debug(_("Option values: %s") % options)
    return options


def set_cvdev_parameter(cv_prefix: Option[str]) -> str:
    """Set the cvdev parameter"""
    cvdev = None
    if cv_prefix:
        cvdev = cv_prefix
    else:
        cvdev = generate_tmp_layer_name("cvdev")
    return cvdev


def cross_validate(
    points: str,
    tension_list: list[int],
    smoothing_list: list[float],
    prefix_cv: str,
    **kwargs: dict,
) -> list[str]:
    """Cross-validate v.surf.rst parameters"""
    gs.message(_("Starting cross-validation..."))

    # Remove tension and smooth from kwargs
    # to avoid passing them to v.surf.rst
    args_blacklist = {
        "point_cloud",
        "output_file",
        "smooth",
        "tension",
        "cv_prefix",
        "format",
    }
    kwargs_copy = {k: v for k, v in kwargs.items() if k not in args_blacklist}

    output_list = []
    # TODO: Add support for multiple processes without user accidently overwhelming the cpu
    for t in tension_list:
        for s in smoothing_list:
            output_name = f"{prefix_cv}_{t}_{str(s).replace('.', '')}"
            try:
                gs.run_command(
                    "v.surf.rst",
                    **kwargs_copy,
                    input=points,
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
    try:
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
    except CalledModuleError as e:
        gs.fatal(_("Error extracting residuals: %s") % e.stderr)
    except ValueError as e:
        gs.fatal(_("Error parsing residuals: %s") % e)
    except ZeroDivisionError as e:
        gs.fatal(_("Error calculating RMSE/MAE: %s") % e)
    except Exception as e:
        gs.fatal(_("Unexpected error: %s") % e)


def cvdev_results(cvdev_list: list[str]) -> list[dict]:
    """Extract RMSE and MAE from cross-validation results"""
    results_list = []
    gs.message(_("Extracting residuals..."))
    for cvdev, tension, smooth in cvdev_list:
        rmse, mae = extract_residuals(cvdev)
        results_list.append(
            {"tension": tension, "smooth": smooth, "rmse": rmse, "mae": mae}
        )

    return results_list


def write_output_file(results: str, output_file: str) -> None:
    if output_file:
        try:
            gs.message(_("Results written to %s") % output_file)
            Path(output_file).write_text(results)
        except Exception as e:
            gs.fatal(_("Error writing output file: %s") % e)


def report_results(results_list: list[dict], format: str) -> None:
    """Report the results of the cross-validation"""
    gs.message(_("Generating results..."))
    if format == "json":
        json_results = json.dumps(results_list, indent=4)
        sys.stdout.write(json_results)
        return json_results
    else:
        header = "Tension,Smoothing,RMSE,MAE\n"
        sys.stdout.write(header)
        for res in results_list:
            sys.stdout.write(
                f"{res['tension']},{res['smooth']},{res['rmse']},{res['mae']}\n"
            )

        csv_results = "\n".join(
            [",".join([str(res[k]) for k in res]) for res in results_list]
        )
        csv_results = f"{header}{csv_results}"
        return csv_results


def set_deviations_colors(map_name: str, data_type: str) -> None:
    """
    Set deviations raster colors.
    The color scheme is from https://ncsu-geoforall-lab.github.io/geospatial-modeling-course/grass/interpolation_2.html

    name: map_name
    type: str
        Name of the map layer to set colors for.
    data_type: str
        Type of the map layer (e.g., raster, vector).
    """
    # Calculate percentiles for color scheme
    try:
        stats = gs.parse_command("r.univar", map=map_name, flags="ge", quiet=True)
        min_val = float(stats["min"])
        max_val = float(stats["max"])
        p1 = float(stats["first_quartile"])
        p2 = float(stats["median"])
        p3 = float(stats["third_quartile"])
    except CalledModuleError as e:
        gs.fatal(_("Error calculating statistics: %s") % e.stderr)

    color_scheme = f"""
        {min_val} red
        {p1} yellow
        {p2} 220:220:220
        {p3} cyan
        {max_val} blue
        """

    if data_type == "raster":
        try:
            gs.write_command(
                "r.colors", map=map_name, rules="-", stdin=color_scheme, quiet=True
            )
        except CalledModuleError as e:
            gs.fatal(_("Error setting raster colors: %s") % e.stderr)
    elif data_type == "vector":
        try:
            gs.write_command(
                "v.colors",
                map=map_name,
                rules="-",
                use="attr",
                column="flt1",
                stdin=color_scheme,
                quiet=True,
            )
        except CalledModuleError as e:
            gs.fatal(_("Error setting vector colors: %s") % e.stderr)
    else:
        gs.fatal(_("Unsupported data type: %s") % data_type)


def compute_deviation_surface(cv_map_list: list[tuple[str, str, str]]) -> None:
    """
    Compute the deviation surface from the cross-validation
    points and write it to a raster map.
    """
    gs.message(_("Computing deviation surfaces..."))
    for cvdev_map, tension, smooth in cv_map_list:
        try:
            gs.run_command(
                "v.surf.rst",
                input=cvdev_map,
                elevation=cvdev_map,
                zcolumn="flt1",
                npmin=140,
                quiet=True,
            )
        except CalledModuleError as e:
            gs.fatal(_("Error computing deviation surface: %s") % e.stderr)

        # Set the color scheme for the deviation surface
        set_deviations_colors(cvdev_map, "vector")
        set_deviations_colors(cvdev_map, "raster")


def main():
    # Required options
    point_cloud = options["point_cloud"]

    # Output options
    output_file = options.get("output_file")
    format = options["format"]

    # Set parameters
    cvdev = set_cvdev_parameter(options.get("cv_prefix"))
    tension = set_default_parameters(
        options.get("tension"), default_option=DEFAULT_SMOOTHING
    )
    smoothing = set_default_parameters(
        options.get("smooth"), default_option=DEFAULT_SMOOTHING
    )

    # Run cross-validation
    cv_map_list = cross_validate(
        points=point_cloud,
        tension_list=tension,
        smoothing_list=smoothing,
        prefix_cv=cvdev,
        **options,  # Pass the options to the cross-validation function kwargs
    )

    # Compute deviation surfaces if cv_prefix is set
    # This will create a raster map for each cvdev_map
    # with the deviations from the original points
    if options.get("cv_prefix"):
        compute_deviation_surface(cv_map_list)

    # Process the results
    # Extract RMSE and MAE from the cvdev maps
    results_list = cvdev_results(cv_map_list)

    if results_list:
        gs.message(_("\nBest parameter combination"))
        # Sort the results by RMSE
        best_combination = min(results_list, key=lambda x: x["rmse"])
        gs.message(_("-" * 50 + "\n"))
        gs.message(_("Tension: %s") % best_combination["tension"])
        gs.message(_("Smoothing: %s") % best_combination["smooth"])
        gs.message(_("RMSE: %s") % best_combination["rmse"])
        gs.message(_("MAE: %s") % best_combination["mae"])
        gs.message(_("-" * 50 + "\n"))
    else:
        gs.warning(
            _("No results found. Unable to determine the best parameter combination.")
        )

    # Report the results
    results = report_results(results_list, format)
    write_output_file(results, output_file)

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
