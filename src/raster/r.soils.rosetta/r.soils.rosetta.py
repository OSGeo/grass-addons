#!/usr/bin/env python

##############################################################################
# MODULE:    r.soils.rosetta
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Estimate van Genuchten soil hydraulic parameters from soil
#            texture using the ROSETTA pedotransfer model.
#
# SPDX-FileCopyrightText: 2026 by Corey T. White and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later.
#
##############################################################################

"""Estimate van Genuchten soil hydraulic parameters from soil texture using
the ROSETTA pedotransfer model."""

# %module
# % description: Estimate van Genuchten soil hydraulic parameters from soil texture using the ROSETTA pedotransfer model.
# % keyword: raster
# % keyword: soil
# % keyword: hydrology
# % keyword: pedotransfer
# %end

# %option G_OPT_R_INPUT
# % key: sand
# % description: Sand content raster map [percent, 0-100]
# % guisection: Inputs
# %end

# %option G_OPT_R_INPUT
# % key: silt
# % description: Silt content raster map [percent, 0-100]
# % guisection: Inputs
# %end

# %option G_OPT_R_INPUT
# % key: clay
# % description: Clay content raster map [percent, 0-100]
# % guisection: Inputs
# %end

# %option G_OPT_R_INPUT
# % key: bulk_density
# % required: no
# % description: Bulk density raster map [g/cm3] (enables ROSETTA model 3)
# % guisection: Inputs
# %end

# %option G_OPT_R_INPUT
# % key: water_content_33
# % required: no
# % description: Volumetric water content at 33 kPa raster map [cm3/cm3] (enables ROSETTA model 4)
# % guisection: Inputs
# %end

# %option G_OPT_R_INPUT
# % key: water_content_1500
# % required: no
# % description: Volumetric water content at 1500 kPa raster map [cm3/cm3] (enables ROSETTA model 5)
# % guisection: Inputs
# %end

# %option
# % key: version
# % type: integer
# % required: no
# % options: 1,2,3
# % answer: 3
# % description: ROSETTA model calibration version (3 = Zhang and Schaap 2017)
# % guisection: Inputs
# %end

# %option G_OPT_R_OUTPUT
# % key: theta_r
# % required: no
# % description: Output residual water content raster map [cm3/cm3]
# % guisection: Outputs
# %end

# %option G_OPT_R_OUTPUT
# % key: theta_s
# % required: no
# % description: Output saturated water content raster map [cm3/cm3]
# % guisection: Outputs
# %end

# %option G_OPT_R_OUTPUT
# % key: alpha
# % required: no
# % description: Output van Genuchten alpha raster map [1/cm]
# % guisection: Outputs
# %end

# %option G_OPT_R_OUTPUT
# % key: n
# % required: no
# % description: Output van Genuchten n raster map [dimensionless]
# % guisection: Outputs
# %end

# %option G_OPT_R_OUTPUT
# % key: ksat
# % required: no
# % description: Output saturated hydraulic conductivity raster map
# % guisection: Outputs
# %end

# %option
# % key: ksat_units
# % type: string
# % required: no
# % options: mm_per_hour,cm_per_day
# % answer: mm_per_hour
# % description: Units for the ksat output map
# % guisection: Outputs
# %end

# %flag
# % key: u
# % description: Also write per-parameter uncertainty (standard deviation) maps as <output>_stddev
# %end

# %rules
# % requires: water_content_33,bulk_density
# % requires: water_content_1500,water_content_33
# %end

import sys
from gettext import gettext as _

import grass.script as gs

# Column indices of the ROSETTA parameter arrays returned per soil sample.
THETA_R, THETA_S, ALPHA, NPAR, KSAT = range(5)

# ROSETTA reports Ksat in cm/day; SIMWE and most GRASS soil tools use mm/hr.
CM_PER_DAY_TO_MM_PER_HOUR = 10.0 / 24.0

# ROSETTA API used only when the local rosetta-soil package is not installed.
ROSETTA_API_URL = "https://www.handbook60.org/api/v2/rosetta/{version}"

# Sentinel written for cells without a prediction. r.in.bin marks NULL by exact
# equality (x == anull); a NaN sentinel fails that test in C, so use a value no
# van Genuchten parameter can take.
NULL_SENTINEL = -999999.0


def _load_backend(version):
    """Return a predict callable and a backend name.

    The predict callable takes a 2D float array (one row per soil sample,
    columns in ROSETTA order) and returns ``(mean, stdev, codes)`` where
    ``mean`` holds the van Genuchten parameters in linear units
    (theta_r, theta_s, alpha [1/cm], n, Ksat [cm/day]). ``stdev`` is ``None``
    when the backend cannot report uncertainty.

    Prefers the offline ``rosetta-soil`` package; falls back to the
    handbook60.org web API when it is not installed.
    """
    import numpy as np

    try:
        from rosetta import rosetta as rosetta_predict, SoilData
    except ImportError:
        return _make_api_backend(version), "api"

    def predict(samples):
        mean, stdev, codes = rosetta_predict(version, SoilData.from_array(samples))
        mean = np.asarray(mean, dtype=np.float64).copy()
        stdev = np.asarray(stdev, dtype=np.float64)
        # The package returns log10(alpha), log10(n), log10(Ksat); the residual
        # and saturated water contents are already linear.
        mean[:, ALPHA : KSAT + 1] = np.power(10.0, mean[:, ALPHA : KSAT + 1])
        return mean, stdev, np.asarray(codes)

    return predict, "package"


def _make_api_backend(version):
    """Build a predict callable backed by the handbook60.org ROSETTA API."""
    import json
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

    import numpy as np

    url = ROSETTA_API_URL.format(version=version)

    def predict(samples):
        # estimate_type "linear" makes the service return arithmetic-mean
        # parameters in linear units, matching the package path after its
        # log10 back-transform.
        payload = json.dumps({"X": samples.tolist(), "estimate_type": "linear"}).encode(
            "utf-8"
        )
        request = Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            gs.fatal(
                _("ROSETTA API HTTP error {code}: {reason}").format(
                    code=error.code, reason=error.reason
                )
            )
        except URLError as error:
            gs.fatal(
                _("ROSETTA API connection error: {reason}").format(reason=error.reason)
            )
        except json.JSONDecodeError:
            gs.fatal(_("ROSETTA API did not return valid JSON."))

        mean = np.asarray(result["van_genuchten_params"], dtype=np.float64)
        codes = np.asarray(result.get("model_codes", []))
        return mean, None, codes

    return predict


def _ordered_inputs(options):
    """Return the input map names in the fixed ROSETTA column order.

    ROSETTA reads columns positionally: sand, silt, clay, bulk density, water
    content at 33 kPa, water content at 1500 kPa. The ``requires`` parser
    rules guarantee no gaps, so appending until the first unset option yields
    a contiguous, valid input set that selects model code 2-5.
    """
    names = [options["sand"], options["silt"], options["clay"]]
    for key in ("bulk_density", "water_content_33", "water_content_1500"):
        if not options[key]:
            break
        names.append(options[key])
    return names


def _read_inputs(names):
    """Read input maps into a stacked float array and a validity mask.

    Returns ``(samples, valid_mask)`` where ``samples`` holds one row per valid
    cell (all inputs finite) and ``valid_mask`` is a flat boolean array mapping
    those rows back onto the current region.
    """
    import numpy as np
    import grass.script.array as garray

    columns = []
    valid = None
    for name in names:
        # Force float64 so integer source maps still map NULL to NaN.
        data = garray.array(mapname=name, null=np.nan, dtype=np.float64)
        flat = np.asarray(data).reshape(-1)
        finite = np.isfinite(flat)
        valid = finite if valid is None else (valid & finite)
        columns.append(flat)

    samples = np.column_stack([col[valid] for col in columns])
    return samples, valid


def _write_output(name, values, valid, overwrite):
    """Scatter per-cell ``values`` back onto the region and write a raster."""
    import numpy as np
    import grass.script.array as garray

    out = garray.array(dtype=np.float64)
    flat = out.reshape(-1)
    flat[...] = NULL_SENTINEL
    flat[valid] = values
    out.write(mapname=name, null=NULL_SENTINEL, overwrite=overwrite)
    gs.raster_history(name, overwrite=True)


def main():
    import numpy as np

    options, flags = gs.parser()

    version = int(options["version"])
    ksat_units = options["ksat_units"]
    write_stddev = flags["u"]
    overwrite = gs.overwrite()

    # Map each requested output option to its ROSETTA parameter column.
    output_columns = {
        "theta_r": THETA_R,
        "theta_s": THETA_S,
        "alpha": ALPHA,
        "n": NPAR,
        "ksat": KSAT,
    }
    requested = {key: options[key] for key in output_columns if options[key]}
    if not requested:
        gs.fatal(
            _(
                "No output requested. Set at least one of: "
                "theta_r, theta_s, alpha, n, ksat."
            )
        )

    input_names = _ordered_inputs(options)
    predict, backend = _load_backend(version)
    if backend == "api":
        gs.warning(
            _(
                "The rosetta-soil package is not installed; using the "
                "handbook60.org web API. Install it with 'pip install "
                "rosetta-soil' for offline, reproducible runs."
            )
        )
    gs.verbose(
        _("Using ROSETTA version {v}, model code {c} ({n} input maps).").format(
            v=version, c=len(input_names), n=len(input_names)
        )
    )

    samples, valid = _read_inputs(input_names)
    if samples.shape[0] == 0:
        gs.fatal(_("No cells with valid data in all input maps."))

    # ROSETTA output depends only on the input tuple, so predict once per
    # unique combination and expand. This is a large speedup for categorical
    # inputs (e.g. SSURGO map units) and harmless for continuous inputs.
    unique_samples, inverse = np.unique(samples, axis=0, return_inverse=True)
    gs.verbose(
        _("Predicting {u} unique soil samples from {t} valid cells.").format(
            u=unique_samples.shape[0], t=samples.shape[0]
        )
    )
    mean, stdev, _codes = predict(unique_samples)
    mean = mean[inverse]
    if stdev is not None:
        stdev = stdev[inverse]

    if write_stddev and stdev is None:
        gs.warning(_("Uncertainty maps are unavailable from the ROSETTA API backend."))

    for key, out_name in requested.items():
        column = output_columns[key]
        values = mean[:, column]
        if key == "ksat" and ksat_units == "mm_per_hour":
            values = values * CM_PER_DAY_TO_MM_PER_HOUR
        _write_output(out_name, values, valid, overwrite)
        gs.verbose(_("Wrote <{name}>.").format(name=out_name))

        if write_stddev and stdev is not None:
            # The package reports alpha/n/Ksat uncertainty in log10 space; the
            # documentation explains the interpretation. No unit conversion is
            # applied to the standard deviation.
            _write_output(f"{out_name}_stddev", stdev[:, column], valid, overwrite)

    gs.message(_("ROSETTA estimation complete."))


if __name__ == "__main__":
    sys.exit(main())
