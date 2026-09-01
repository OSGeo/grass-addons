#!/usr/bin/env python3

"""MODULE:      i.sentinel3.import
AUTHOR(S):   Stefan Blumentrath
PURPOSE:     Import and pre-process Sentinel-3 data from the Copernicus program
COPYRIGHT:   (C) 2024-202-20255 BY Norwegian Water and Energy Directorate,
Stefan Blumentrath, and the GRASS development team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

# %Module
# % description: Import and pre-process Sentinel-3 data from the Copernicus program
# % keyword: imagery
# % keyword: satellite
# % keyword: Sentinel
# % keyword: import
# % keyword: optical
# % keyword: thermal
# %end

# %option
# % key: input
# % label: Sentinel-3 input data
# % description: Either a (commaseparated list of) path(s) to Sentinel-3 zip files or a textfile with such paths (one per row)
# % required: yes
# % multiple: yes
# %end

# %option
# % key: product_type
# % multiple: no
# % options: S3SL1RBT,S3SL2LST
# % answer: S3SL2LST
# % description: Sentinel-3 product type to import (currently, only S3SL1RBT and S3SL2LST are supported)
# % required: yes
# %end

# %option
# % key: bands
# % multiple: yes
# % answer: all
# % required: yes
# % description: Data bands to import (e.g. LST, default is all available)
# %end

# %option
# % key: anxillary_bands
# % multiple: yes
# % required: no
# % description: Anxillary data bands to import (e.g. LST_uncertainty, default is None, use "all" to import all available)
# %end

# %option
# % key: flag_bands
# % multiple: yes
# % required: no
# % description: Quality flag bands to import (e.g. bayes_in, default is None, use "all" to import all available)
# %end

# %option
# % key: basename
# % description: Basename used as prefix for map names (default is derived from the input file(s))
# % required: no
# %end

# %option G_OPT_F_OUTPUT
# % key: register_output
# % description: Name for output file to use with t.register
# % required: no
# %end

# %option G_OPT_M_DIR
# % key: metadata
# % description: Name of directory into which Sentinel metadata json dumps are saved
# % required: no
# %end

# %option
# % key: maximum_solar_angle
# % type: double
# % description: Import only pixels where solar angle is lower or equal to the given maximum
# % required: no
# %end

# %option G_OPT_M_NPROCS
# %end

# to be implemented
# # %flag
# # % key: a
# # % description: Apply cloud mask before import (can significantly speed up import)
# # % guisection: Settings
# # %end

# %flag
# % key: c
# % description: Import LST in degree celsius (default is kelvin)
# % guisection: Settings
# %end

# %flag
# % key: d
# % description: Import data with decimals as double precision
# % guisection: Settings
# %end

# to be implemented
# # %flag
# # % key: e
# # % description: Import also elevation from geocoding of stripe
# # % guisection: Settings
# # %end

# %flag
# % key: n
# % description: Import data at native resolution of the bands (default is use current region)
# % guisection: Settings
# %end

# %flag
# % key: j
# % description: Write metadata json for each band to LOCATION/MAPSET/cell_misc/BAND/description.json
# % guisection: Settings
# %end

# %flag
# % key: k
# % description: Keep original cell values during interpolation (see: r.fill.stats)
# % guisection: Settings
# %end

# %flag
# % key: o
# % description: Process oblique view (default is nadir)
# % guisection: Settings
# %end

# %flag
# % key: r
# % description: Rescale radiance bands to reflectance
# % guisection: Settings
# %end

# # %rules
# # % excludes: -p,register_output
# # %end


# TODO
# - implement printing
# - implement cloud-masking at import
# - implement elevation import
# - do not write to temporary file (feed r.in.xyz from stdin)
# - Add orphaned pixels

from __future__ import annotations

import atexit
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import grass.script as gs
from grass.pygrass.modules import Module, MultiModule, ParallelModuleQueue
from grass.temporal.datetime_math import (
    datetime_to_grass_datetime_string as grass_timestamp,
)
from typing import Optional

S3_SUPPORTED_PRODUCTS = ["S3SL1RBT", "S3SL2LST"]

S3_SOLAR_FLUX = {
    "S3SL1RBT": {
        "band": "{}_solar_irradiance_{}",
        "nc_file": "{}_quality_{}.nc",
        # See: https://github.com/senbox-org/s3tbx/blob/master/s3tbx-rad2refl/src/main/java/org/esa/s3tbx/processor/rad2refl/Rad2ReflConstants.java
        "defaults": {
            "S1": 1837.39,
            "S2": 1525.94,
            "S3": 956.17,
            "S4": 365.90,
            "S5": 248.33,
            "S6": 78.33,
        },
    },
    "S3SL2LST": None,
}

S3_FILE_PATTERN = {
    "S3OL1ERF": None,
    "S3SL1RBT": "S3*SL_1_RBT*.zip",
    "S3SL2LST": "S3*SL_2_LST*.zip",
}

S3_SUN_PARAMTERS = {
    "S3OL1ERF": None,
    "S3SL1RBT": {
        "geocoding": {
            "nc_file": "geodetic_tx.nc",
            "bands": {"lat": "latitude_tx", "lon": "longitude_tx"},
        },
        "sun_bands": {
            "nc_file": "geometry_t{}.nc",
            "bands": {
                "solar_azimuth": "solar_azimuth_t{}",
                "solar_zenith": "solar_zenith_t{}",
            },
        },
    },
    "S3SL2LST": None,
}

S3_GRIDS = {
    "S3OL1ERF": None,
    "S3SL2LST": {"i": 1000.0},
    "S3SL1RBT": {
        "a": 500.0,  # Stripe A
        "b": 500.0,  # Stripe B
        "c": 1000.0,  # TDI grid
        "f": 500.0,  # F channel grid
        "i": 1000.0,  # 1km grid
    },
}

# Default view is n (nadir), o = oblique
S3_VIEWS = {
    "S3OL1ERF": None,
    "S3SL1RBT": ["o", "n"],
    "S3SL2LST": ["n"],
}

S3_RADIANCE_ADJUSTMENT = {
    "S3_PN_SLSTR_L1_08": {
        "n": {
            # Nadir
            "S1": 0.97,
            "S2": 0.98,
            "S3": 0.98,
            "S5": 1.11,
            "S6": 1.13,
        },
        "o": {
            # Oblique
            "S1": 0.94,
            "S2": 0.95,
            "S3": 0.95,
            "S5": 1.04,
            "S6": 1.07,
        },
    },
}

S3_BANDS = {
    "bands": {
        "S3OL1ERF": None,
        "S3SL1RBT": {
            "F1": {
                "geometries": ("f",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "BT",
            },
            "F2": {
                "geometries": ("i",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "BT",
            },
            "S1": {
                "geometries": ("a",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "radiance",
                "exception": "{}_{}_{}",
            },
            "S2": {
                "geometries": ("a",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "radiance",
                "exception": "{}_{}_{}",
            },
            "S3": {
                "geometries": ("a",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "radiance",
                "exception": "{}_{}_{}",
            },
            "S4": {
                "geometries": ("a", "b"),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "radiance",
                "exception": "{}_{}_{}",
            },
            "S5": {
                "geometries": ("a", "b"),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "radiance",
                "exception": "{}_{}_{}",
            },
            "S6": {
                "geometries": ("a", "b"),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "radiance",
                "exception": "{}_{}_{}",
            },
            "S7": {
                "geometries": ("i",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "BT",
            },
            "S8": {
                "geometries": ("i",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "BT",
            },
            "S9": {
                "geometries": ("i",),
                "nc_file": "{}_{}_{}.nc",
                "full_name": "{}_{}_{}",
                "types": "BT",
            },
        },
        "S3SL2LST": {
            "LST": {
                "geometries": ("i",),
                "nc_file": "{}_{}.nc",
                "full_name": "{}",
                "types": None,
                "exception": "exception",
            },
            "LST_uncertainty": {
                "geometries": ("i",),
                "nc_file": "LST_in.nc",
                "full_name": "{}",
                "types": None,
                "exception": "exception",
            },
        },
    },
    "flags": {
        "S3OL1ERF": None,
        "S3SL1RBT": {
            "bayes": {
                "geometries": ("a", "b", "f", "i"),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "cloud": {
                "geometries": ("a", "b", "f", "i"),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "confidence": {
                "geometries": ("a", "b", "f", "i"),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "pointing": {
                "geometries": ("a", "b", "f", "i"),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "probability_cloud_dual": {
                "geometries": ("i",),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "probability_cloud_single": {
                "geometries": ("i",),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
        },
        "S3SL2LST": {
            "bayes": {
                "geometries": ("i",),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "cloud": {
                "geometries": ("i",),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "confidence": {
                "geometries": ("i",),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "probability_cloud_dual": {
                "geometries": ("i",),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
            "probability_cloud_single": {
                "geometries": ("i",),
                "nc_file": "flags_{}.nc",
                "full_name": "{}_{}",
                "types": None,
            },
        },
    },
    "anxillary": {
        "S3OL1ERF": None,
        "S3SL1RBT": None,
        "S3SL2LST": {
            "biome": {
                "geometries": ("i",),
                "nc_file": "LST_ancillary_ds.nc",
                "full_name": "{}",
                "types": None,
            },
            "fraction": {
                "geometries": ("i",),
                "nc_file": "LST_ancillary_ds.nc",
                "full_name": "{}",
                "types": None,
            },
            "NDVI": {
                "geometries": ("i",),
                "nc_file": "LST_ancillary_ds.nc",
                "full_name": "{}",
                "types": None,
            },
            "TCWV": {
                "geometries": ("i",),
                "nc_file": "LST_ancillary_ds.nc",
                "full_name": "{}",
                "types": None,
            },
        },
    },
}

# GRASS map precision
DTYPE_TO_GRASS = {
    "float32": "FCELL",
    "uint16": "CELL",
    "uint8": "CELL",
    "float64": "FCELL",
}

OVERWRITE = gs.overwrite()

GISENV = gs.gisenv()
TMP_FILE = Path(gs.tempfile(create=False))
TMP_FILE.mkdir(exist_ok=True, parents=True)
TMP_NAME = gs.tempname(12)

SUN_ZENITH_ANGLE = None


def cleanup() -> None:
    """Remove all temporary data."""
    # remove temporary maps
    if TMP_FILE:
        gs.try_remove(TMP_FILE)

    # Remove external data if mapset uses r.external.out
    external = gs.parse_key_val(gs.read_command("r.external.out", flags="p"), sep=": ")
    if "directory" in external:
        for map_file in Path(external["directory"]).glob(
            f"{TMP_NAME}_*{external['extension']}",
        ):
            if map_file.is_file():
                map_file.unlink()

    gs.run_command(
        "g.remove",
        type="raster",
        pattern=f"{TMP_NAME}_*",
        flags="f",
        quiet=True,
    )


def np_as_scalar(var: np.dtype) -> str | int | float:
    """Return a numpy object as scalar."""
    if type(var).__module__ == np.__name__:
        if var.size > 1:
            return str(var)
        return var.item()
    return var


def get_dtype_range(np_datatype: str) -> dict:
    """Get information to set the valid data range based on dtype.

    dtype range according to:
    https://docs.unidata.ucar.edu/netcdf-c/current/attribute_conventions.html#valid_range
    """
    if np_datatype == "bool":
        return {"min": 0, "max": 1, "reolution": 1}

    dtype = np.dtype(np_datatype)
    if not np.issubdtype(dtype, np.floating) and not np.issubdtype(dtype, np.integer):
        gs.fatal(_("Unsupported data type {}").format(np_datatype))

    # Integer dtypes
    if "int" in np_datatype:
        dt_info = np.iinfo(np_datatype)
        return {"min": dt_info.min, "max": dt_info.max, "resolution": 1}

    # Float dtypes
    dt_info = np.finfo(np_datatype)
    return {
        "min": dt_info.min,
        "max": dt_info.max,
        "resolution": 2.0 * dt_info.resolution,
    }


def consolidate_metadata_dicts(metadata_dicts: dict) -> dict:
    """Consolidate a list of metadata dictionaries for all input scenes.

    Consolidate a list of metadata dictionaries for all
    input scenes into unified metadata for the resulting map
    """
    map_metadata_dicts = {}
    for map_dict in metadata_dicts:
        for map_name, meta_dict in map_dict.items():
            if map_name not in map_metadata_dicts:
                map_metadata_dicts[map_name] = {}
            for meta_key, meta_value in meta_dict.items():
                if meta_key not in map_metadata_dicts[map_name]:
                    map_metadata_dicts[map_name][meta_key] = meta_value
                elif (
                    isinstance(map_metadata_dicts[map_name][meta_key], list)
                    and meta_value not in map_metadata_dicts[map_name][meta_key]
                ):
                    if isinstance(meta_value, (list, set)):
                        map_metadata_dicts[map_name][meta_key].extend(meta_value)
                    else:
                        map_metadata_dicts[map_name][meta_key].append(meta_value)
                elif meta_value != map_metadata_dicts[map_name][meta_key]:
                    if isinstance(map_metadata_dicts[map_name][meta_key], (list, set)):
                        if meta_value not in map_metadata_dicts[map_name][meta_key]:
                            map_metadata_dicts[map_name][meta_key].append(meta_value)
                    else:
                        map_metadata_dicts[map_name][meta_key] = [
                            map_metadata_dicts[map_name][meta_key],
                            meta_value,
                        ]
    return map_metadata_dicts


def write_metadata(json_dict: dict, metadatajson: str) -> None:
    """Write extended map metadata to JSON file."""
    with Path(metadatajson).open("w", encoding="UTF8") as outfile:
        json.dump(json_dict, outfile)


def convert_units(np_column: np.array, from_u: str, to_u: str) -> np.array:
    """Convert units of a numpy array.

    Converts a numpy column from one unit to
    another, convertibility needs to be checked beforehand.
    """
    try:
        from cf_units import Unit
    except ImportError:
        gs.fatal(
            _(
                "Could not import cf_units. Please install it with:\n"
                "'pip install cf_units'!",
            ),
        )

    try:
        converted_col = Unit(from_u).convert(np_column, Unit(to_u))
    except ValueError:
        gs.fatal(
            _("Warning: Could not convert units from {from_u} to {to_u}.").format(
                from_u=from_u,
                to_u=to_u,
            ),
        )
        converted_col = np_column

    return converted_col


def extend_region(region_dict: dict, additional_region_dict: dict) -> dict:
    """Extend region bounds in region_dict to cover also the additional_region_dict."""
    region_dict["n"] = max(region_dict["n"], additional_region_dict["n"])
    region_dict["e"] = max(region_dict["e"], additional_region_dict["e"])
    region_dict["s"] = min(region_dict["s"], additional_region_dict["s"])
    region_dict["w"] = min(region_dict["w"], additional_region_dict["w"])
    return region_dict


def adjust_region(region_dict: dict) -> dict:
    """Adjust region bounds for r.in.xyz.

    Adjust region bounds for r.in.xyz (bounds + half resolution)
    aligned to resolution in ew and ns direction
    starting from the sw-corner
    """
    nsres = int(region_dict["nsres"])
    ewres = int(region_dict["ewres"])
    ns_round_to = 10 ** (len(str(nsres)) - len(str(nsres).rstrip("0")))
    ew_round_to = 10 ** (len(str(ewres)) - len(str(ewres).rstrip("0")))
    region_dict["s"] = (
        np.floor((region_dict["s"] - (nsres / 2.0)) / ns_round_to) * ns_round_to
    )
    region_dict["w"] = (
        np.floor((region_dict["w"] - (ewres / 2.0)) / ew_round_to) * ew_round_to
    )
    region_dict["n"] = (
        region_dict["s"]
        + np.ceil((region_dict["n"] + (nsres / 2.0) - region_dict["s"]) / nsres) * nsres
    )
    region_dict["e"] = (
        region_dict["w"]
        + np.ceil((region_dict["e"] + (ewres / 2.0) - region_dict["w"]) / ewres) * ewres
    )
    return region_dict


def intersect_region(
    region_current: dict,
    region_stripe: dict,
    *,
    align_current: bool = True,
) -> dict:
    """Intersect stripe region with current region aligned to resolution and extended for r.in.xyz.

    Adjust region bounds for r.in.xyz to the intersection
    of the current region (bounds + half resolution)
    aligned to resolution in ew and ns direction
    starting from the sw-corner
    """
    # Remove potential, irrelevant / conflicting dict-keys and convert to float
    relevant_keys = ["n", "s", "e", "w", "nsres", "ewres"]
    region_current = {
        region_key: float(region_current[region_key]) for region_key in relevant_keys
    }
    region_stripe = {
        region_key: float(region_stripe[region_key]) for region_key in relevant_keys
    }
    region_dict = region_current.copy()
    # Choose pixel alignment with stripe or region
    if not align_current:
        region_dict.update(
            {"nsres": region_stripe["nsres"], "ewres": region_stripe["ewres"]},
        )
    for direction in "nsew":
        resolution = region_dict["nsres"] if direction in "ns" else region_dict["ewres"]
        if direction in "ne":
            # Get the intersection of the stripe and the current region
            region_dict[direction] = min(
                region_current[direction],
                region_stripe[direction],
            )
            # Align region to required resolution and extend by one pixel for r.in.xyz
            region_dict[direction] = (
                np.ceil(region_dict[direction] / resolution) * resolution + resolution
            )
        else:
            region_dict[direction] = max(
                region_current[direction],
                region_stripe[direction],
            )
            region_dict[direction] = (
                np.floor(region_dict[direction] / resolution) * resolution - resolution
            )
    return region_dict


def parse_s3_file_name(file_name: str) -> dict:
    """Extract info from file name according to ESA naming onvention.

    Naming convention is documented here:
    https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-3-slstr/naming-convention
    Assumes that file name is checked to be a valid / supported Sentinel-3 file name

    :param file_name: string representing the file name of a Senintel-3 scene
    """
    try:
        return {
            "mission_id": file_name[0:3],
            "instrument": file_name[4:6],
            "level": file_name[7],
            "product": file_name[9:12],
            "start_time": datetime.strptime(file_name[16:31], "%Y%m%dT%H%M%S"),
            "end_time": datetime.strptime(file_name[32:47], "%Y%m%dT%H%M%S"),
            "ingestion_time": datetime.strptime(file_name[48:63], "%Y%m%dT%H%M%S"),
            "duration": file_name[64:68],
            "cycle": file_name[69:72],
            "relative_orbit": file_name[73:76],
            "frame": file_name[77:81],
            "producer": file_name[82:85],
            "product_class": file_name[86:87],
            "timeliness": file_name[88:90],
            "baseline_collection": file_name[91:94],
        }
    except ValueError:
        gs.fatal(_("{} is not a supported Sentinel-3 scene").format(str(file_name)))


def extract_file_info(s3_files: list, basename: str | None = None) -> tuple[str, dict]:
    """Extract information from file name according to naming conventions."""
    result_dict = {}
    product_track_ids = [
        "cycle",
        "relative_orbit",
        "producer",
        "product_class",
        "timeliness",
        "baseline_collection",
    ]
    for s3_file in s3_files:
        file_info = parse_s3_file_name(s3_file.name)
        if not result_dict:
            result_dict = file_info
            result_dict["start_time"] = file_info["start_time"]
            result_dict["end_time"] = file_info["end_time"]
            result_dict["frame"] = {file_info["frame"]}
            for pid in product_track_ids:
                result_dict[pid] = {file_info[pid]}
        else:
            if file_info["mission_id"] != result_dict["mission_id"]:
                result_dict["mission_id"] = "S3_"
            result_dict["start_time"] = min(
                result_dict["start_time"],
                file_info["start_time"],
            )
            result_dict["end_time"] = max(
                result_dict["end_time"],
                file_info["end_time"],
            )
            for pid in product_track_ids:
                result_dict[pid].add(file_info[pid])
            result_dict["frame"].add(file_info["frame"])
    for pid in product_track_ids:
        if len(result_dict[pid]) > 1:
            gs.warning(
                _("Merging {key} {values}").format(
                    key=pid,
                    values=", ".join(result_dict[pid]),
                ),
            )
    if result_dict["mission_id"] == "3_":
        gs.warning(_("Merging Seninel-3A and Seninel-3B data"))
    if not basename:
        basename = "_".join(
            [
                result_dict["mission_id"],
                result_dict["instrument"],
                result_dict["level"],
                result_dict["product"],
                result_dict["start_time"].strftime("%Y%m%d%H%M%S"),
                result_dict["end_time"].strftime("%Y%m%d%H%M%S"),
                *[next(iter(result_dict[pid])) for pid in product_track_ids],
            ],
        )
    return (
        basename,
        result_dict,
    )


def get_geocoding(
    zip_file: ZipFile,
    root: Path,
    geo_bands_dict: dict,
    sun_mask: np.array = None,
    region_bounds: dict | None = None,
) -> tuple[dict, np.array, list[int]]:
    """Get ground control points from NetCDF file."""
    member = str(root / geo_bands_dict["nc_file"])
    nc_file_path = zip_file.extract(member, path=TMP_FILE)
    with Dataset(nc_file_path) as nc_file_open:
        nc_bands = OrderedDict()
        resolution = nc_file_open.resolution.strip(" ").split(" ")[1:3]

        for band_id, band in geo_bands_dict["bands"].items():
            if band not in nc_file_open.variables:
                gs.fatal(
                    _(
                        "{s3_file} does not contain a container {container} with band {band}",
                    ).format(
                        s3_file=str(Path(nc_file_path).parent.name),
                        container=geo_bands_dict["nc_file"],
                        band=", ".join(band),
                    ),
                )

            # Add band to dict
            nc_bands[band_id] = nc_file_open[band][:]

        # Create initial mask
        if sun_mask is not None:
            mask = np.logical_or(sun_mask, nc_bands["lat"][:].mask)
        else:
            mask = nc_bands["lat"][:].mask

        if region_bounds:
            # Mask to region
            mask = np.ma.mask_or(
                mask,
                np.ma.masked_outside(
                    nc_bands["lon"],
                    float(region_bounds["ll_w"]),
                    float(region_bounds["ll_e"]),
                ).mask,
            )
            mask = np.ma.mask_or(
                mask,
                np.ma.masked_outside(
                    nc_bands["lat"],
                    float(region_bounds["ll_s"]),
                    float(region_bounds["ll_n"]),
                ).mask,
            )

            if mask.all():
                gs.warning(
                    _("No valid pixels inside computational region found in {}").format(
                        str(zip_file.filename),
                    ),
                )
                return None, None, None
    return nc_bands, mask, resolution


def setup_import_multi_module(
    tmp_ascii: Path,
    mapname: str,
    distance: float | None = None,
    fill_flags: str | bool = False,
    zrange: tuple[float, float] | None = None,
    val_col: int | None = None,
    data_type: str | None = None,
    method: str = "mean",
    solar_flux: float | None = None,
    rules: str | None = None,
) -> list[Module]:
    """Set up GRASS GIS moduls for importing S3 bands."""
    # Basic import module
    modules = [
        Module(
            "r.in.xyz",
            input=str(tmp_ascii),
            output=f"{TMP_NAME}_{mapname}",
            method=method,
            separator=",",
            x=1,
            y=2,
            # Array contains a column z at position 3 (with all 0)
            # after coordinate transformation
            z=val_col,
            flags="i",
            type=data_type,
            zrange=zrange,
            percent=100,
            run_=False,
            verbose=False,
            quiet=True,
            overwrite=OVERWRITE,
        ),
    ]

    # Interpolation of missing / empty pixels
    interp_mod = Module(
        "r.fill.stats",
        flags=fill_flags,
        input=f"{TMP_NAME}_{mapname}",
        mode="wmean" if method == "mean" else "mode",
        cells=3,
        distance=distance,
        power=2.0,
        run_=False,
        quiet=True,
        overwrite=OVERWRITE,
    )
    # Add conversion from radiance to reflectance if requested and relevant
    if solar_flux:
        interp_mod.outputs.output = f"{TMP_NAME}_{mapname}_rad"
        modules.append(interp_mod)
        mapname_reflectance = mapname.replace("radiance", "reflectance")
        # Create mapcalc module
        modules.append(
            Module(
                "r.mapcalc",
                expression=f"{mapname_reflectance}={TMP_NAME}_{mapname}_rad * ({np.pi} / {solar_flux} / cos({SUN_ZENITH_ANGLE}))",
                quiet=True,
                overwrite=OVERWRITE,
                run_=False,
            ),
        )
        mapname = mapname_reflectance
    else:
        interp_mod.outputs.output = mapname
        modules.append(interp_mod)

    # Add categories (for flag datasets)
    if rules:
        modules.append(
            Module(
                "r.category",
                quiet=True,
                map=mapname,
                rules="-",
                stdin_=rules,
                separator=":",
                run_=False,
            ),
        )
    return modules


def get_file_metadata(nc_dataset: Dataset) -> dict:
    """Collect metadata from NetCDF file."""
    metadata = {
        attr: np_as_scalar(nc_dataset.getncattr(attr))
        for attr in [
            "title",
            "creation_time",
            "absolute_orbit_number",
            "track_offset",
            "start_offset",
            "institution",
            "references",
            "resolution",
            "source",
            "contact",
            "comment",
            "history",
            "processing_baseline",
            "product_name",
        ]
        if attr in nc_dataset.ncattrs()
    }
    metadata["start_time"] = parse_timestr(nc_dataset.start_time)
    metadata["end_time"] = parse_timestr(nc_dataset.stop_time)
    metadata["history"] = metadata["history"].strip()

    return metadata


def get_band_metadata(
    band_tuple: tuple,
    nc_variable: np.array,
    fmt: str,
    file_metadata: dict | None = None,
    basename: str | None = None,
    to_celsius: bool = False,
) -> tuple[dict, str]:
    """Extract band metadata from NetCDF variable."""
    metadata = file_metadata.copy()
    # Collect metadata
    band_attrs = nc_variable.ncattrs()

    # Define variable name
    varname_short = band_tuple[1]
    datatype = str(nc_variable[:].dtype)

    # Define map name
    mapname = f"{basename}_{varname_short}"
    metadata["mapname"] = mapname

    # Define unit
    unit = nc_variable.units if "units" in band_attrs else None
    unit = "degree_celsius" if band_tuple[0].startswith("LST") and to_celsius else unit
    metadata["unit"] = unit

    # Define datatype and import method
    if datatype not in DTYPE_TO_GRASS:
        gs.fatal(
            _("Unsupported datatype {dt} in band {band}").format(
                dt=datatype,
                band=band_tuple[1],
            ),
        )
    if datatype in {"uint8", "uint16"}:
        metadata["method"] = "max"  # Unfortunately there is no "mode" in r.in.xyz
        fmt += ",%i"
    else:
        metadata["method"] = "mean"
        fmt += ",%.12f"
    metadata["datatype"] = DTYPE_TO_GRASS[datatype]

    # Compile description
    for time_reference in ["start_time", "end_time"]:
        metadata[time_reference] = metadata[time_reference].isoformat()
    metadata["description"] = (
        json.dumps(metadata, separators=["\n", ": "]).lstrip("{").rstrip("}")
    )

    # Handle offset, scale, and valid data range, see:
    # https://docs.unidata.ucar.edu/netcdf-c/current/attribute_conventions.html
    metadata["zrange"] = None
    min_val, max_val = None, None
    if "valid_range" in band_attrs:
        min_val, max_val = nc_variable.valid_range
    if "valid_min" in band_attrs:
        min_val = nc_variable.valid_min
    if "valid_max" in band_attrs:
        max_val = nc_variable.valid_max
    data_range = get_dtype_range(datatype)
    if "_FillValue" in band_attrs:
        fill_val = nc_variable._FillValue
        if fill_val > 0:
            min_val = data_range["min"] if min_val is None else min_val
            max_val = (
                fill_val - 1 if max_val is None else max_val
            )  # data_range["resolution"]
        elif fill_val <= 0:
            min_val = (
                fill_val + 1 if min_val is None else min_val
            )  # data_range["resolution"]
            max_val = data_range["max"] if max_val is None else max_val
    else:
        min_val = (
            data_range["min"] + 1 if min_val is None else min_val
        )  # data_range["resolution"]
        max_val = data_range["max"] if max_val is None else max_val

    if "flag_masks" in band_attrs:
        min_val = min(nc_variable.flag_masks)
        max_val = max(nc_variable.flag_masks)

    metadata["description"] += f"\n\nvalid_min: {min_val}\nvalid_max: {max_val}"
    metadata["zrange"] = [min_val, max_val]
    metadata["semantic_label"] = f"S3_{varname_short}"

    return metadata, fmt


def transform_coordinates(coordinates: np.array) -> np.array:
    """Tranform coordinates to projection of the current location.

    Tranforms a numpy array with coordinates to the
    projection of the current location
    """
    # Create source coordinate reference
    s_srs = osr.SpatialReference()
    s_srs.ImportFromEPSG(4326)

    # Create target coordinate reference
    t_srs = osr.SpatialReference()
    t_srs.ImportFromWkt(gs.read_command("g.proj", flags="fw"))

    # Initialize osr transformation
    transform = osr.CoordinateTransformation(s_srs, t_srs)

    return (
        coordinates[:, [1, 0]]
        if s_srs.IsSame(t_srs)
        else np.array(transform.TransformPoints(coordinates))[:, [0, 1]]
    )


def write_xyz(
    tmp_ascii: str,
    nc_bands: np.array,
    mask: np.array,
    fmt: str | None = None,
    project: bool = True,
) -> None:
    """Write temporary XYZ ascii file."""
    # Extract grid coordinates
    lon = np.ma.masked_where(mask, nc_bands["lon"][:]).compressed()
    lat = np.ma.masked_where(mask, nc_bands["lat"][:]).compressed()

    if project:
        # Project coordinates
        np_output = transform_coordinates(
            np.dstack((lat, lon)).reshape(lat.shape[0], 2),
        )
    else:
        np_output = np.hstack((lon[:, None], lat[:, None]))
    # Fetch, mask and stack requested bands
    for band in nc_bands:
        if band in {"lat", "lon"}:
            continue
        add_array = nc_bands[band][:]
        if np.ma.is_masked(add_array):
            add_array = add_array.filled()
        np_output = np.hstack(
            (np_output, np.ma.masked_where(mask, add_array).compressed()[:, None]),
        )

    # Write to temporary file
    tmp_ascii_path = Path(tmp_ascii)
    if tmp_ascii_path.exists():
        with tmp_ascii_path.open("ab") as tmp_ascii_file:
            np.savetxt(tmp_ascii_file, np_output, delimiter=",", fmt=fmt)
    else:
        np.savetxt(tmp_ascii, np_output, delimiter=",", fmt=fmt)

    return {
        "n": np.ma.max(np_output[:, 1]),
        "s": np.ma.min(np_output[:, 1]),
        "e": np.ma.max(np_output[:, 0]),
        "w": np.ma.min(np_output[:, 0]),
    }


def import_s3(
    s3_file: str,
    kwargs: dict,
    s3_product: str | None = None,
) -> tuple[dict, list[str], dict]:
    """Import Sentinel-3 netCDF4 data."""
    # Unpack dictionary variables
    rmap = kwargs["meta_dict"][0]
    region_bounds = kwargs["reg_bounds"]
    mod_flags = kwargs["mod_flags"]
    module_queue = {}
    region_dicts = {}
    register_strings = []

    with ZipFile(s3_file) as zip_file:
        members = zip_file.namelist()
        root = members[0].rsplit(".SEN3", maxsplit=1)[0]
        root = Path(f"{root}.SEN3")
        # Check if solar flux raster band is required
        sun_region_bounds = region_bounds.copy()
        if mod_flags["r"] or kwargs["maximum_solar_angle"]:
            tmp_ascii_sun = TMP_FILE / f"{rmap}_sun_parameters.txt"
            (
                module_queue,
                register_output,
                sun_region_dict,
            ) = s3_product.get_sun_parameters(
                zip_file,
                root,
                rmap,
                tmp_ascii_sun,
                region_bounds,
                maximum_solar_angle=kwargs["maximum_solar_angle"],
            )
            register_strings.append(register_output)
            if module_queue is None:
                return None, None, None
            region_dicts["sun_parameters"] = sun_region_dict

            if kwargs["maximum_solar_angle"]:
                sun_region_dict = intersect_region(
                    dict(kwargs["current_reg"]),
                    sun_region_dict,
                    align_current=False,
                )

                if sun_region_dict["e"] <= sun_region_dict["w"]:
                    # East is wrapped around meridian
                    if sun_region_dict["e"] <= float(kwargs["current_reg"]["w"]):
                        sun_region_dict["e"] = float(kwargs["current_reg"]["e"])
                    # West is wrapped around meridian
                    if sun_region_dict["w"] >= float(kwargs["current_reg"]["e"]):
                        sun_region_dict["w"] = float(kwargs["current_reg"]["w"])

                sun_region_bounds = gs.parse_command(
                    "g.region",
                    flags="ugb",
                    quiet=True,
                    **sun_region_dict,
                )

        for stripe, stripe_dict in s3_product.requested_stripe_content.items():
            # Could be parallelized!!!
            # Get geocoding (lat/lon, elevation) and initial mask
            tmp_ascii = TMP_FILE / f"{rmap}_{stripe}.txt"
            nc_bands, mask, resolution = get_geocoding(
                zip_file,
                root,
                stripe_dict["geocoding"],
                region_bounds=sun_region_bounds,
            )
            if nc_bands is None:
                return None, None, None
            fmt = ",".join(["%.12f"] * len(nc_bands))
            for nc_file, bands in stripe_dict["containers"].items():
                (
                    nc_bands,
                    module_queue,
                    register_output,
                    fmt,
                ) = s3_product.process_nc_file(
                    zip_file,
                    root,
                    (nc_file, bands),
                    nc_bands,
                    rmap,
                    module_queue,
                    mod_flags,
                    tmp_ascii,
                    fmt=fmt,
                )
                register_strings.append(register_output)
            stripe_region_dict = write_xyz(
                tmp_ascii,
                nc_bands,
                mask,
                fmt=fmt,
                project=True,
            )
            stripe_region_dict["ewres"] = float(resolution[0])
            stripe_region_dict["nsres"] = float(resolution[1])

            if kwargs["maximum_solar_angle"]:
                sun_region_dict_intersect = intersect_region(
                    dict(kwargs["current_reg"]),
                    sun_region_dict,
                    align_current=False,
                )

                region_dicts[stripe] = intersect_region(
                    sun_region_dict_intersect,
                    stripe_region_dict,
                    align_current=False,
                )
            else:
                region_dicts[stripe] = stripe_region_dict
    return module_queue, register_strings, region_dicts


class S3Product:
    """Class for Senintel-3 data products.

    The class provides information necessary to pre-process Senintel-3 data products
    level 1 and 2.
    """

    def __init__(
        self,
        product_type: str,
        view: str = "n",
        bands: list[str] | str | None = None,
        flag_bands: list[str] | str | None = None,
        anxillary_bands: list[str] | str | None = None,
    ) -> None:
        """Initialize a Sentinel-3 product."""
        self.product_type = product_type
        self.available_views = S3_VIEWS[product_type]
        self.available_bands = list(S3_BANDS["bands"][product_type].keys())
        self.available_flag_bands = list(S3_BANDS["flags"][product_type].keys())
        self.available_anxillary_bands = (
            list(S3_BANDS["anxillary"][product_type].keys())
            if S3_BANDS["anxillary"][product_type]
            else None
        )
        self.view = self._check_view(view)
        self.bands = self._check_bands(bands)
        self.flag_bands = self._check_bands(flag_bands, band_type="flag_bands")
        self.anxillary_bands = self._check_bands(
            anxillary_bands,
            band_type="anxillary_bands",
        )
        self.grids = S3_GRIDS[product_type]
        self.requested_stripe_content = self._collect_requested_stripe_content()
        self.file_pattern = S3_FILE_PATTERN[product_type]

    def __str__(self) -> str:
        """Return Sentinel-3 product information as JSON."""
        return json.dumps(self.__repr__(), indent=2)

    def __repr__(self) -> str:
        """Return Sentinel-3 product information as JSON."""
        class_dict = self.__dict__.copy()
        for band_type in ["bands", "flag_bands", "anxillary_bands"]:
            bands_of_type = getattr(self, band_type)
            class_dict[band_type] = (
                {
                    band: description.__dict__ if description else None
                    for band, description in bands_of_type.items()
                }
                if bands_of_type
                else None
            )
        return json.dumps(class_dict, indent=2)

    def _check_view(self, view: str) -> str:
        """Check requested Satellite view to process."""
        if view not in self.available_views:
            gs.warning(
                _("View {} not available for product type {}").format(
                    view,
                    self.product_type,
                ),
            )
        return view

    def _check_bands(
        self,
        bands: list[str] | str,
        band_type: str = "bands",
    ) -> list[S3Band]:
        """Check requested Satellite bands to process."""
        band_types = {
            "bands": self.available_bands,
            "flag_bands": self.available_flag_bands,
            "anxillary_bands": self.available_anxillary_bands,
        }
        if not band_types[band_type]:
            return None
        if not bands:
            if not bands and band_type == "bands":
                gs.warning(_("At least one band band needs to be given"))
            return None
        if bands == "all":
            bands = band_types[band_type]
        band_objects = {}
        for band in bands:
            if band not in band_types[band_type]:
                gs.warning(
                    _("Band {0} is not available in product_type {1}").format(
                        band,
                        self.product_type,
                    ),
                )
            band_objects[band] = S3Band(self.product_type, band, use_b=False, view="n")
        return band_objects

    def _collect_requested_stripe_content(self) -> dict:
        """Collect requested stripe content."""
        suffixes = {}
        for band_type in ["bands", "flag_bands", "anxillary_bands"]:
            selected_bands = getattr(self, band_type)
            if not selected_bands:
                continue
            for band_id, band_object in selected_bands.items():
                if band_object.suffix in suffixes:
                    if "containers" not in suffixes[band_object.suffix]:
                        suffixes[band_object.suffix]["containers"] = {}
                    if (
                        band_object.nc_file
                        in suffixes[band_object.suffix]["containers"]
                    ):
                        suffixes[band_object.suffix]["containers"][
                            band_object.nc_file
                        ].append(band_id)
                    else:
                        suffixes[band_object.suffix]["containers"][
                            band_object.nc_file
                        ] = [band_id]
                else:
                    suffixes[band_object.suffix] = {
                        "containers": {band_object.nc_file: [band_id]},
                        "geocoding": {
                            "nc_file": f"geodetic_{band_object.suffix}.nc",
                            "bands": {
                                "lat": f"latitude_{band_object.suffix}",
                                "lon": f"longitude_{band_object.suffix}",
                                "elevation": f"elevation_{band_object.suffix}",
                            },
                        },
                    }
        return suffixes

    def process_nc_file(
        self,
        zip_file: ZipFile,
        root: Path,
        container_dict_items: tuple,
        nc_bands: list,
        prefix: str,
        module_queue: dict,
        module_flags: dict,
        tmp_ascii: str,
        fmt: str | None = None,
    ) -> tuple[list, dict, dict, str]:
        """Extract requested bands as numpy arrays from NetCDF file and setup import modules."""
        meta_information = {}
        member = str(root / container_dict_items[0])
        nc_file_path = zip_file.extract(member, path=TMP_FILE)
        with Dataset(nc_file_path) as nc_file_open:
            file_metadata = get_file_metadata(nc_file_open)
            for band in container_dict_items[1]:
                # Check for band
                solar_flux = None
                if band in self.bands:
                    band = self.bands[band]
                    if band.solar_flux and module_flags["r"]:
                        solar_flux = band.get_solar_flux(
                            zip_file,
                            root,
                        )
                elif band in self.flag_bands:
                    band = self.flag_bands[band]
                elif band in self.anxillary_bands:
                    band = self.anxillary_bands[band]
                if band.full_name not in nc_file_open.variables:
                    gs.fatal(
                        _(
                            "{s3_file} does not contain a container {container} with band {band}",
                        ).format(
                            s3_file=str(root),
                            container=band.nc_file,
                            band=", ".join(band.full_name),
                        ),
                    )

                nc_variable = nc_file_open[band.full_name]
                # Apply radiance adjustment
                if band.radiance_adjustment and module_flags["r"]:
                    add_array = nc_variable[:] * band.radiance_adjustment
                else:
                    add_array = nc_variable[:]

                # Collect band metadata
                metadata = get_band_metadata(
                    (band.band_id, band.full_name),
                    nc_variable,
                    fmt,
                    file_metadata=file_metadata,
                    basename=prefix,
                    to_celsius=module_flags["c"],
                )
                fmt = metadata[1]

                # Get solar flux for band
                metadata[0]["solar_flux"] = solar_flux

                if band.exception:
                    maximum_exception = 3
                    if np.ma.is_masked(add_array):
                        add_array.mask = np.ma.mask_or(
                            add_array.mask,
                            nc_file_open[band.exception][:] >= maximum_exception,
                        )
                    else:
                        add_array = np.ma.masked_array(
                            add_array,
                            nc_file_open[band.exception][:] >= maximum_exception,
                        )
                if np.ma.is_masked(add_array):
                    add_array = add_array.filled()

                # Rescale temperature variables if requested
                if band.full_name == "LST" and module_flags["c"]:
                    add_array = convert_units(add_array, "K", "degree_celsius")

                # Write metadata json if requested
                band_attrs = nc_file_open[band.full_name].ncattrs()

                # Define categories for flag datasets
                rules = None
                if "flag_masks" in band_attrs:
                    rules = "\n".join(
                        [
                            ":".join(
                                [
                                    str(nc_file_open[band.full_name].flag_masks[idx]),
                                    label,
                                ],
                            )
                            for idx, label in enumerate(
                                nc_file_open[band.full_name].flag_meanings.split(" "),
                            )
                        ],
                    )
                # Setup import modules
                fill_flags = "m"
                if not module_flags["d"] and metadata[0]["datatype"] != "CELL":
                    fill_flags += "s"
                if module_flags["k"]:
                    fill_flags += "k"
                module_queue[band.full_name] = setup_import_multi_module(
                    tmp_ascii,
                    metadata[0]["mapname"],
                    distance=2.0 * band.resolution,
                    fill_flags=fill_flags,
                    zrange=metadata[0]["zrange"],
                    val_col=len(nc_bands) + 1,
                    data_type=metadata[0]["datatype"],
                    method=metadata[0]["method"],
                    solar_flux=solar_flux,
                    rules=rules,
                )

                # Add array with invalid data masked to ordered dict of nc_bands
                nc_bands[band.full_name] = add_array

                meta_information[metadata[0]["mapname"]] = {
                    "semantic_label": metadata[0]["semantic_label"],
                    "unit": metadata[0]["unit"],
                    **{
                        a: np_as_scalar(nc_file_open.getncattr(a))
                        for a in nc_file_open.ncattrs()
                    },
                    "variable": band.full_name,
                    **{
                        a: np_as_scalar(nc_file_open[band.full_name].getncattr(a))
                        for a in nc_file_open[band.full_name].ncattrs()
                    },
                }

            return nc_bands, module_queue, meta_information, fmt

    def get_sun_parameters(
        self,
        zip_file: ZipFile,
        root: Path,
        prefix: str,
        tmp_ascii: str,
        region_bounds: dict,
        maximum_solar_angle: float | None = None,
    ) -> tuple[dict, dict, dict]:
        """Extract sun parameters from S3 SLSTR product.

        Oriented on:
        https://github.com/sertit/eoreader/blob/main/eoreader/products/optical/s3_slstr_product.py#L862
        """
        # Get values
        import_modules = {}
        meta_information = {}
        fmt = "%.12f,%.12f"
        member = str(
            root
            / S3_SUN_PARAMTERS[self.product_type]["sun_bands"]["nc_file"].format(
                self.view,
            ),
        )
        nc_file_path = zip_file.extract(member, path=TMP_FILE)
        with Dataset(nc_file_path) as sun_parameter_nc:
            file_metadata = get_file_metadata(sun_parameter_nc)
            if maximum_solar_angle:
                sun_mask = sun_parameter_nc[
                    S3_SUN_PARAMTERS[self.product_type]["sun_bands"]["bands"][
                        "solar_zenith"
                    ].format(self.view)
                ][:] >= float(maximum_solar_angle)
            nc_bands, mask, resolution = get_geocoding(
                zip_file,
                root,
                S3_SUN_PARAMTERS[self.product_type]["geocoding"],
                sun_mask=sun_mask if maximum_solar_angle and np.any(sun_mask) else None,
                region_bounds=region_bounds,
            )
            if nc_bands is None:
                return None, None, None

            for band_id, band in S3_SUN_PARAMTERS[self.product_type]["sun_bands"][
                "bands"
            ].items():
                band = band.format(self.view)
                sun_parameter_array = sun_parameter_nc[band]

                metadata = get_band_metadata(
                    (band_id, band),
                    sun_parameter_array,
                    fmt,
                    file_metadata=file_metadata,
                    basename=prefix,
                )

                fmt += ",%.12f"
                nc_bands[band_id] = sun_parameter_array[:]
                map_name = f"{prefix}_{band_id}"
                if band_id == "solar_zenith":
                    global SUN_ZENITH_ANGLE
                    SUN_ZENITH_ANGLE = map_name
                import_modules[band_id] = setup_import_multi_module(
                    tmp_ascii,
                    map_name,
                    distance=3,
                    fill_flags="ks",
                    zrange=[-32767, 32768],
                    val_col=len(nc_bands),
                    data_type="FCELL",
                    method="mean",
                    solar_flux=None,
                )
                meta_information[map_name] = {
                    "semantic_label": f"S3_{band_id}",
                    "unit": metadata[0]["unit"],
                    **{
                        a: np_as_scalar(sun_parameter_nc.getncattr(a))
                        for a in sun_parameter_nc.ncattrs()
                    },
                    "variable": band,
                    **{
                        a: np_as_scalar(sun_parameter_nc[band].getncattr(a))
                        for a in sun_parameter_nc[band].ncattrs()
                    },
                }

            # Write to temporary file
            sun_region_dict = write_xyz(
                tmp_ascii,
                nc_bands,
                mask,
                fmt=fmt,
                project=True,
            )
            sun_region_dict["ewres"], sun_region_dict["nsres"] = (
                float(
                    resolution[0],
                ),
                float(resolution[1]),
            )

        return import_modules, meta_information, sun_region_dict


class S3Band:
    """Class for properties and methods related to Sentinel-3 bands."""

    def __init__(
        self,
        product_type: str,
        band_id: str,
        use_b: bool = False,
        view: str = "n",
        radiance_adjustment: str = "S3_PN_SLSTR_L1_08",
    ) -> None:
        """Initialize a Sentinel-3 band."""
        self.band_id = band_id
        self.band_type = self._get_band_type(product_type)
        # Need to call in this order
        geometry = self._get_geometry(product_type, use_b)
        self.resolution = S3_GRIDS[product_type][geometry]
        self.suffix = f"{geometry}{view}"
        self.full_name = self._get_full_name(product_type)
        self.exception = self._get_exception_band(product_type)
        self.nc_file = self._get_nc_file(product_type)
        self.radiance_adjustment = self._get_radiance_adjustment(
            radiance_adjustment,
            view,
        )
        self.solar_flux = self._get_solar_flux_dict_for_band(product_type)

    def __str__(self) -> str:
        """Return a JSON representation of the S3Band instance."""
        return json.dumps(self.__repr__(), indent=2)

    def __repr__(self) -> str:
        """Return a JSON representation of the S3Band instance."""
        return json.dumps(self.__dict__, indent=2)

    def _get_band_type(self, product_type: str) -> str | None:
        for band_type, s3_bands in S3_BANDS.items():
            if self.band_id in s3_bands[product_type]:
                return band_type
        gs.fatal(_("Oh no"))
        return None

    def _get_geometry(self, product_type: str, use_b: bool) -> str:
        band_dict = S3_BANDS[self.band_type][product_type][self.band_id]
        return (
            "b"
            if use_b and "b" in band_dict["geometries"]
            else band_dict["geometries"][0]
        )

    def _get_full_name(self, product_type: str) -> str:
        band_dict = S3_BANDS[self.band_type][product_type][self.band_id]
        types = band_dict["types"]
        if self.band_type != "bands":
            return band_dict["full_name"].format(self.band_id, self.suffix)
        if types:
            return band_dict["full_name"].format(self.band_id, types, self.suffix)
        return band_dict["full_name"].format(self.band_id, self.suffix)

    def _get_nc_file(self, product_type: str) -> str:
        band_dict = S3_BANDS[self.band_type][product_type][self.band_id]
        types = band_dict["types"]
        if self.band_type == "flags":
            return band_dict["nc_file"].format(self.suffix)
        if types:
            return band_dict["nc_file"].format(self.band_id, types, self.suffix)
        return band_dict["nc_file"].format(self.band_id, self.suffix)

    def _get_radiance_adjustment(
        self,
        radiance_adjustment: str,
        view: str,
    ) -> float | None:
        if radiance_adjustment not in S3_RADIANCE_ADJUSTMENT:
            gs.fatal("Missing information on radiance adjustment")
        if self.band_id in S3_RADIANCE_ADJUSTMENT[radiance_adjustment][view]:
            return S3_RADIANCE_ADJUSTMENT[radiance_adjustment][view][self.band_id]
        return None

    def _get_exception_band(self, product_type: str) -> dict | None:
        if "exception" in S3_BANDS[self.band_type][product_type][self.band_id]:
            return S3_BANDS[self.band_type][product_type][self.band_id][
                "exception"
            ].format(self.band_id, "exception", self.suffix)
        return None

    def _get_solar_flux_dict_for_band(self, product_type: str) -> dict | None:
        if (
            S3_SOLAR_FLUX[product_type]
            and self.band_id in S3_SOLAR_FLUX[product_type]["defaults"]
        ):
            return {
                "default": S3_SOLAR_FLUX[product_type]["defaults"][self.band_id],
                "band": S3_SOLAR_FLUX[product_type]["band"].format(
                    self.band_id,
                    self.suffix,
                ),
                "nc_file": S3_SOLAR_FLUX[product_type]["nc_file"].format(
                    self.band_id,
                    self.suffix,
                ),
            }
        return None

    def get_solar_flux(self, zip_file: ZipFile, root_path: Path) -> float:
        """Get solar spectral flux in mW / (m^2 * sr * nm) for band.

        :returns: solar Flux
        :type: float

        """
        if not self.solar_flux:
            return None
        member = str(root_path / self.solar_flux["nc_file"])
        nc_file_path = zip_file.extract(member, path=TMP_FILE)
        sf_dataset = Dataset(nc_file_path)
        solar_flux = np.nanmean(sf_dataset[self.solar_flux["band"]])
        if np.isnan(solar_flux):
            solar_flux = self.solar_flux["default"]
        return float(solar_flux)

    def _get_band_geo_points(self, suffix: str) -> dict:
        """Get ground control point references from suffix."""
        if self.suffix.startswith("t"):
            return None
        return {
            "nc_file": f"geodetic_{suffix}.nc",
            "lat": f"latitude_{suffix}",
            "lon": f"longitude_{suffix}",
            "elevation": f"elevation_{suffix}",
        }

    def adjust_radiance(self, np_band_array: np.array) -> np.array:
        """Get radiance adjustment for band object."""
        if not self.radiance_adjustment:
            return np_band_array * self.radiance_adjustment
        return np_band_array


def get_solar_angle_bounds(region_bounds: dict, sun_region_dict: dict) -> dict:
    """Get latlon coordinates of bounds in solar angle bands."""
    solar_bounds = gs.parse_command("g.region", flags="ugl", **sun_region_dict)
    solar_bounds["ll_n"] = max(
        float(solar_bounds["nw_lat"]),
        float(solar_bounds["ne_lat"]),
    )
    solar_bounds["ll_s"] = min(
        float(solar_bounds["sw_lat"]),
        float(solar_bounds["se_lat"]),
    )
    if solar_bounds["ll_n"] < float(region_bounds["ll_n"]):
        region_bounds["ll_n"] = solar_bounds["ll_n"]
    if float(solar_bounds["ll_s"]) > float(region_bounds["ll_s"]):
        region_bounds["ll_s"] = solar_bounds["ll_s"]
    return region_bounds


def check_region_validity(stripe_id: str, stripe_region: dict) -> None:
    """Check if the computational region is valid and exit if not."""
    if (
        stripe_region["s"] >= stripe_region["n"]
        or stripe_region["w"] >= stripe_region["e"]
    ):
        gs.warning(
            _(
                "No valid data found in data stripe {}.\n"
                "Nothing to import with the given input.",
            ).format(stripe_id),
        )
        sys.exit(0)


def _get_grass_metadata(grass_md: dict, md_field: str) -> str | None:
    md_field = grass_md.get(md_field)
    if isinstance(md_field, list):
        return ",".join(md_field)
    return md_field


def main() -> None:
    """Do the main work."""
    pattern = re.compile(
        ".*" + S3_FILE_PATTERN[options["product_type"]].replace("*", ".*"),
    )

    # check provided input
    s3_files = options["input"].split(",")
    if len(s3_files) == 1 and re.match(pattern, s3_files[0]) is None:
        try:
            s3_files = Path(s3_files[0]).read_text(encoding="UTF8").strip().split("\n")
        except ValueError:
            gs.fatal(
                _(
                    "Input <{}> is neither a supported Sentinel-3 scene nor a text file with scenes",
                ).format(options["input"]),
            )

    if not s3_files:
        gs.warning("No scenes found to process, please check input.")
        sys.exit()

    s3_files = [Path(scene) for scene in s3_files]
    for s3_scene in s3_files:
        if not s3_scene.exists():
            gs.fatal(_("Input file <{sn}> not found").format(sn=str(s3_scene)))
        if not re.match(pattern, s3_scene.name):
            gs.fatal(
                _(
                    "Input <{sn}> is not a supported Sentinel-3 scene for the requested product type <{pt}>",
                ).format(sn=s3_scene, pt=options["product_type"]),
            )

    if flags["d"]:
        global DTYPE_TO_GRASS
        DTYPE_TO_GRASS["float64"] = "DCELL"

    solar_bands = S3_SUN_PARAMTERS[options["product_type"]]
    solar_bands = solar_bands.get("sun_bands").get("bands") if solar_bands else {}

    s3_product = S3Product(
        options["product_type"],
        view="o" if flags["o"] else "n",
        bands=options["bands"],
        flag_bands=options["flag_bands"],
        anxillary_bands=options["anxillary_bands"],
    )

    meta_info_dict = extract_file_info(s3_files, basename=options["basename"])

    if gs.parse_command("g.proj", flags="g")["proj"] == "ll":
        gs.fatal(_("Running in lonlat location is currently not supported"))

    nprocs = int(options["nprocs"])

    # Get region bounds
    region_bounds = gs.parse_command("g.region", flags="ugb", quiet=True)
    current_region = gs.parse_command("g.region", flags="ug")

    # Collect variables for import
    import_dict = {
        "reg_bounds": dict(region_bounds),
        "current_reg": dict(current_region),
        "mod_flags": flags,
        "meta_dict": meta_info_dict,
        "maximum_solar_angle": float(options["maximum_solar_angle"])
        if options["maximum_solar_angle"]
        else None,
    }

    module_queues = []
    register_strings = []
    region_dicts = {}
    region_list = []

    for s3_file in s3_files:
        gs.verbose(_("Preparing scene {} for import").format(s3_file.name))
        module_list, register_string, region_dict = import_s3(
            s3_file,
            import_dict,
            s3_product=s3_product,
        )
        if module_list is not None:
            module_queues.append(module_list)
            register_strings.extend(register_string)
            region_list.append(region_dict)
            if not region_dicts:
                region_dicts = region_dict.copy()
            else:
                for stripe_id, region in region_dict.items():
                    if stripe_id not in region_dicts:
                        region_dicts[stripe_id] = region
                    else:
                        extend_region(region_dicts[stripe_id], region)
    if not module_queues:
        gs.warning(_("Nothing to import with the given input."))
        sys.exit(0)
    stripe_envs = {}
    for stripe_id, stripe_region in region_dicts.items():
        stripe_env = os.environ.copy()
        check_region_validity(stripe_id, stripe_region)

        if flags["n"]:
            stripe_env["GRASS_REGION"] = gs.region_env(**adjust_region(stripe_region))
        else:
            stripe_region_dict = intersect_region(
                dict(current_region),
                stripe_region,
                align_current=stripe_id != "sun_parameters",
            )
            check_region_validity(stripe_id, stripe_region_dict)
            stripe_env["GRASS_REGION"] = gs.region_env(
                **stripe_region_dict,
            )
        stripe_envs[stripe_id] = stripe_env

    if flags["r"]:
        gs.verbose(_("Importing solar parameter bands"))
        queue = ParallelModuleQueue(nprocs)
        compute_env = stripe_envs["sun_parameters"]
        for solar_parameter in solar_bands:
            module_list = []
            for solar_module in module_queues[0][solar_parameter]:
                solar_module.env_ = compute_env
                module_list.append(solar_module)
            queue.put(MultiModule(module_list))
        queue.wait()
        # Here one could zoom to non-null pixels in solar angle map
        # g.region zoom=zolar_zenith
        # if maximum_solar_angle is given in consistently limit
        # imported pixels

    gs.verbose(
        _("Importing scenes {}").format(
            "\n" + "\n".join([s3_file.name for s3_file in s3_files]),
        ),
    )
    queue = ParallelModuleQueue(nprocs)
    for band_id, modules in module_queues[0].items():
        if band_id in solar_bands:
            continue
        # S3SL2LST product has only "in" stripe and band names have no suffix
        if band_id[-2:] not in stripe_envs:
            compute_env = stripe_envs["in"]
        else:
            compute_env = stripe_envs[band_id[-2:]]
        module_list = []
        for listed_module in modules:
            listed_module.env_ = compute_env
            module_list.append(listed_module)
        queue.put(MultiModule(module_list))
    queue.wait()

    # Update map support information and filter out empty maps
    # Empty maps may occure because of a lack of valid data within the comutational region
    t_register_strings = []
    queue = ParallelModuleQueue(nprocs)
    gs.verbose(_("Writing metadata to maps and filtering empty maps..."))
    for mapname, metadata in consolidate_metadata_dicts(register_strings).items():
        mapname = (
            mapname if not flags["r"] else mapname.replace("radiance", "reflectance")
        )
        if not gs.raster_info(mapname)["max"]:
            gs.warning(f"Raster map {mapname} is empty. Removing...")
            gs.run_command(
                "g.remove",
                type="raster",
                name=mapname,
                flags="f",
                quiet=True,
            )
            continue
        metadata["semantic_label"] = (
            metadata["semantic_label"]
            if not flags["r"]
            else metadata["semantic_label"].replace("radiance", "reflectance")
        )
        # Write raster history
        gs.raster_history(mapname, overwrite=True)

        # Write extended metadata if requested
        if flags["j"]:
            json_standard_folder = Path(GISENV["GISDBASE"]).joinpath(
                GISENV["LOCATION_NAME"],
                GISENV["MAPSET"],
                "cell_misc",
                mapname,
            )
            if not json_standard_folder.exists():
                json_standard_folder.mkdir(parents=True, exist_ok=True)

            write_metadata(metadata, str(json_standard_folder / "description.json"))

        description = (
            json.dumps(metadata, separators=["\n", ": "]).lstrip("{").rstrip("}")
        )

        support_kwargs = {
            "map": mapname,
            "title": _get_grass_metadata(metadata, "title"),
            "history": _get_grass_metadata(metadata, "history"),
            "units": metadata.get("unit"),
            "source1": _get_grass_metadata(metadata, "product_name"),
            "source2": _get_grass_metadata(metadata, "processing_baseline"),
            "description": description,
            "semantic_label": metadata.get("semantic_label"),
        }

        queue.put(
            MultiModule(
                [
                    Module(
                        "r.support",
                        **support_kwargs,
                        quiet=True,
                        run_=False,
                    ),
                    Module(
                        "r.timestamp",
                        map=mapname,
                        date="/".join(
                            [
                                grass_timestamp(meta_info_dict[1]["start_time"]),
                                grass_timestamp(meta_info_dict[1]["end_time"]),
                            ],
                        ),
                        quiet=True,
                        run_=False,
                    ),
                ],
            ),
        )
        t_register_strings.append(
            "|".join(
                [
                    f"{mapname}@{GISENV['MAPSET']}",
                    meta_info_dict[1]["start_time"].isoformat(
                        sep=" ",
                        timespec="seconds",
                    ),
                    meta_info_dict[1]["end_time"].isoformat(
                        sep=" ",
                        timespec="seconds",
                    ),
                    metadata["semantic_label"],
                ],
            ),
        )
    queue.wait()

    # Write t.register file if requested
    t_register_strings = "\n".join(t_register_strings) if t_register_strings else ""
    if options["register_output"]:
        gs.verbose(
            _("Writing register file <{}>...").format(options["register_output"]),
        )
        Path(options["register_output"]).write_text(
            t_register_strings + "\n",
            encoding="UTF8",
        )
    else:
        print(t_register_strings)
    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    # Lazy imports
    try:
        from dateutil.parser import isoparse as parse_timestr
    except ImportError:
        gs.fatal(
            _(
                "Could not import dateutil. Please install it with:\n"
                "'pip install dateutil'!",
            ),
        )
    try:
        from osgeo import osr

        osr.UseExceptions()
    except ImportError:
        gs.fatal(
            _("Could not import gdal. Please install it with:\n'pip install GDAL'!"),
        )

    try:
        from netCDF4 import Dataset
    except ImportError:
        gs.fatal(
            _(
                "Could not import netCDF4. Please install it with:\n"
                "'pip install netcdf4'!",
            ),
        )

    try:
        import numpy as np
    except ImportError:
        gs.fatal(
            _(
                "Could not import numpy. Please install it with:\n'pip install numpy'!",
            ),
        )

    atexit.register(cleanup)
    sys.exit(main())
