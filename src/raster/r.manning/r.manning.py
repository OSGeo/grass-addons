#!/usr/bin/env python

##############################################################################
# MODULE:    r.manning
#
# AUTHOR(S): Anna Petrasova <kratochanna@gmail.com>
#
# PURPOSE:   Converts land cover raster to Manning's roughness coefficient raster.
#
# SPDX-FileCopyrightText: 2026 Anna Petrasova
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

"""Converts land cover raster to Manning's roughness coefficient raster."""

# %module
# % description: Converts land cover raster to Manning's roughness coefficient raster.
# % keyword: raster
# % keyword: hydrology
# % keyword: Manning
# % keyword: roughness
# % keyword: land cover
# %end

# %option G_OPT_R_INPUT
# % key: input
# % description: Name of input land cover raster map
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Name of output Manning's n raster map
# %end

# %option
# % key: landcover
# % type: string
# % required: yes
# % options: nlcd,worldcover,custom
# % description: Land cover classification system
# % descriptions: nlcd;National Land Cover Database (NLCD);worldcover;ESA WorldCover;custom;custom created land cover
# %end

# %option
# % key: source
# % type: string
# % required: no
# % options: kalyanapu,hecras
# % answer: kalyanapu
# % description: Land cover-specific source of Manning's n coefficients
# % descriptions: kalyanapu;Kalyanapu et al. 2009 (shallow overland flow, NLCD only);hecras;HEC-RAS 2D Manual for NLCD (deep flow, NLCD only)
# %end

# %option
# % key: method
# % type: string
# % required: no
# % options: low,medium,high,random
# % answer: medium
# % description: Roughness output type
# % descriptions: low;Lower bound estimate;medium;Typical conditions;high;Upper bound estimate;random;Uniform random distribution
# %end

# %option G_OPT_F_INPUT
# % key: rules
# % required: no
# % description: Path to custom rules file (CSV with columns: code,n)
# % guisection: Custom
# %end

# %option G_OPT_M_SEED
# %end

import sys
import random

import grass.script as gs


# Values from Kalyanapu et al. (2009) Table 2
# Min/max ranges estimated using 0.75/1.33 multipliers (except 82).
# 11 from HECRAS, 82 is conventional tillage from McCuen (2005), missing in Kalyanapu
NLCD_KALYANAPU = {
    11: [0.025, 0.040, 0.050],  # Open Water
    21: [0.030, 0.040, 0.054],  # Developed, Open Space
    22: [0.051, 0.068, 0.090],  # Developed, Low Intensity
    23: [0.051, 0.068, 0.090],  # Developed, Medium Intensity
    24: [0.030, 0.040, 0.054],  # Developed, High Intensity
    31: [0.008, 0.011, 0.015],  # Barren Land
    41: [0.270, 0.360, 0.480],  # Deciduous Forest
    42: [0.240, 0.320, 0.430],  # Evergreen Forest
    43: [0.300, 0.400, 0.530],  # Mixed Forest
    52: [0.300, 0.400, 0.530],  # Shrub/Scrub
    71: [0.280, 0.368, 0.490],  # Grassland/Herbaceous
    81: [0.240, 0.325, 0.430],  # Pasture/Hay
    82: [0.080, 0.160, 0.240],  # Cultivated Crops
    90: [0.065, 0.086, 0.110],  # Woody Wetlands
    95: [0.140, 0.183, 0.240],  # Emergent Herbaceous Wetlands
}

# range from HEC-RAS 2D User's Manual Version 6.6
# initial values are roughly estimated using 0.75/1.33 multipliers matching Chow
NLCD_HECRAS = {
    11: [0.025, 0.035, 0.050],  # Open Water
    21: [0.030, 0.040, 0.050],  # Developed, Open Space
    22: [0.060, 0.085, 0.120],  # Developed, Low Intensity
    23: [0.080, 0.100, 0.160],  # Developed, Medium Intensity
    24: [0.120, 0.160, 0.200],  # Developed, High Intensity
    31: [0.023, 0.030, 0.030],  # Barren Land
    41: [0.100, 0.140, 0.200],  # Deciduous Forest
    42: [0.080, 0.120, 0.160],  # Evergreen Forest
    43: [0.080, 0.130, 0.200],  # Mixed Forest
    51: [0.025, 0.035, 0.050],  # Dwarf Scrub
    52: [0.070, 0.100, 0.160],  # Shrub/Scrub
    71: [0.025, 0.035, 0.050],  # Grassland/Herbaceous
    72: [0.025, 0.035, 0.050],  # Sedge/Herbaceous
    81: [0.025, 0.035, 0.050],  # Pasture/Hay
    82: [0.020, 0.030, 0.050],  # Cultivated Crops
    90: [0.045, 0.100, 0.150],  # Woody Wetlands
    95: [0.050, 0.060, 0.085],  # Emergent Herbaceous Wetlands
}

# Values from QGIS Manning's Roughness Generator plugin
# (mabdazzam/mannings_roughness_generator) for ESA WorldCover 2021.
WORLDCOVER_AZZAM = {
    10: [0.070, 0.094, 0.124],  # Tree cover
    20: [0.045, 0.066, 0.096],  # Shrubland
    30: [0.028, 0.033, 0.043],  # Grassland
    40: [0.025, 0.035, 0.045],  # Cropland
    50: [0.016, 0.018, 0.020],  # Built-up
    60: [0.010, 0.023, 0.035],  # Bare/sparse vegetation
    70: [0.010, 0.020, 0.030],  # Snow and ice
    80: [0.025, 0.035, 0.045],  # Permanent water bodies
    90: [0.060, 0.090, 0.120],  # Herbaceous wetland
    95: [0.150, 0.225, 0.300],  # Mangroves
    100: [0.040, 0.060, 0.080],  # Moss and lichen
}


def get_lookup_table(landcover, source):
    """Return the appropriate lookup table based on landcover and source."""
    if landcover == "nlcd":
        if source == "hecras":
            return NLCD_HECRAS
        if source == "kalyanapu":
            return NLCD_KALYANAPU
        gs.fatal(_("source '{}' not available for NLCD").format(source))
    if landcover == "worldcover":
        return WORLDCOVER_AZZAM
    if landcover == "custom":
        return None
    gs.fatal(_("Unknown landcover type: {}").format(landcover))


def parse_custom_rules(rules_file):
    """Parse custom CSV rules file.

    Supports two formats:
        code,n              - single value (used for all levels)
        code,n_low,n_med,n_high - three values for low/medium/high
    """
    lookup = {}
    with open(rules_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) == 2:
                code = int(parts[0])
                n_value = float(parts[1])
                lookup[code] = [n_value, n_value, n_value]
            elif len(parts) >= 4:
                code = int(parts[0])
                lookup[code] = [float(parts[1]), float(parts[2]), float(parts[3])]
            else:
                gs.warning(_("Skipping invalid line: {}").format(line))
    return lookup


def generate_recode_rules(lookup, method):
    """Generate r.recode rules string from lookup table."""
    rules = []
    indices = {"low": 0, "medium": 1, "high": 2}

    if method == "random":
        for code, values in sorted(lookup.items()):
            n_value = random.uniform(values[indices["low"]], values[indices["high"]])
            rules.append(f"{code}:{code}:{n_value}:{n_value}")
    else:
        for code, values in sorted(lookup.items()):
            n_value = values[indices[method]]
            rules.append(f"{code}:{code}:{n_value}:{n_value}")
    return "\n".join(rules)


def recode_map(input_raster, output_raster, lookup, method):
    """Run r.recode with the given lookup table and method."""
    recode_rules = generate_recode_rules(lookup, method)
    gs.write_command(
        "r.recode",
        input=input_raster,
        output=output_raster,
        rules="-",
        stdin=recode_rules,
    )


def main():
    options, flags = gs.parser()
    input_raster = options["input"]
    output_raster = options["output"]
    landcover = options["landcover"]
    source = options["source"]
    method = options["method"]
    rules_file = options["rules"]

    if options["seed"]:
        random.seed(int(options["seed"]))

    # Get lookup table
    if landcover == "custom" or rules_file:
        if not rules_file:
            gs.fatal(_("Custom landcover requires rules file"))
        lookup = parse_custom_rules(rules_file)
    else:
        lookup = get_lookup_table(landcover, source)

    # Generate main output
    recode_map(input_raster, output_raster, lookup, method)
    gs.raster_history(output_raster, overwrite=True)


if __name__ == "__main__":
    sys.exit(main())
