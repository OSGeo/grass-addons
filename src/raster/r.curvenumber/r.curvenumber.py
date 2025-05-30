#!/usr/bin/env python
##############################################################################
# MODULE:    r.curvenumber
#
# AUTHOR(S): Abdullah Azzam <mabdazzam@outlook.com>
#
# PURPOSE:   Generates the Curve Number raster based on landcover and
#            hydrologic soil group rasters
#
# COPYRIGHT: (C) 2025 by Abdullah Azzam and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################
"""It generates the curve number raster based on the land cover and hydrologic soil group rasters"""

# %module
# % description: Generates the Curve Number raster from the landcover and hydrologic soil group rasters
# % keyword: raster
# % keyword: hydrology
# % keyword: curve number
# %end

# %option G_OPT_R_INPUT
# % key: landcover
# % description: Landcover raster
# %end

# %option G_OPT_R_INPUT
# % key: soil
# % description: Hydrologic Soil Group raster
# %end

# %option
# % key: landcover_source
# % type: string
# % description: Lookup table source
# % options: nlcd,esa,custom
# % required: yes
# %end

# %option G_OPT_F_INPUT
# % key: lookup
# % description: CSV with columns lc,hsg,cn (required if source=custom)
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % description: Curve number raster
# %end

import csv
from grass.script import parser, run_command, fatal

# Embedded lookup tables
NLCD_CSV = """lc,hsg,cn
11,1,100
11,2,100
11,3,100
11,4,100
12,1,100
12,2,100
12,3,100
12,4,100
21,1,52
21,2,68
21,3,78
21,4,84
22,1,81
22,2,88
22,3,90
22,4,93
23,1,84
23,2,89
23,3,93
23,4,94
24,1,88
24,2,92
24,3,93
24,4,94
31,1,70
31,2,81
31,3,88
31,4,92
32,1,70
32,2,81
32,3,88
32,4,92
41,1,45
41,2,66
41,3,77
41,4,83
42,1,30
42,2,55
42,3,70
42,4,77
43,1,36
43,2,60
43,3,73
43,4,79
51,1,33
51,2,42
51,3,55
51,4,62
52,1,33
52,2,42
52,3,55
52,4,62
71,1,47
71,2,63
71,3,75
71,4,85
72,1,47
72,2,63
72,3,75
72,4,85
73,1,74
73,2,74
73,3,74
73,4,74
74,1,79
74,2,79
74,3,79
74,4,79
81,1,40
81,2,61
81,3,73
81,4,79
82,1,62
82,2,74
82,3,82
82,4,86
90,1,86
90,2,86
90,3,86
90,4,86
95,1,80
95,2,80
95,3,80
"""

ESA_CSV = """lc,hsg,cn
10,1,36
10,2,60
10,3,73
10,4,79
20,1,55
20,2,72
20,3,81
20,4,86
30,1,49
30,2,69
30,3,79
30,4,84
40,1,50
40,2,62
40,3,73
40,4,78
50,1,89
50,2,92
50,3,94
50,4,95
60,1,65
60,2,79
60,3,87
60,4,90
70,1,0
70,2,0
70,3,0
70,4,0
80,1,100
80,2,100
80,3,100
80,4,100
90,1,80
90,2,80
90,3,80
90,4,80
95,1,0
95,2,0
95,3,0
95,4,0
100,1,74
100,2,77
100,3,78
100,4,79
"""


# CSV parsing helpers
def parse_csv(text):
    """Parse an embedded CSV string into {(lc,hsg): cn}."""
    lut = {}
    for row in csv.DictReader(text.strip().splitlines()):
        lut[row["lc"], row["hsg"]] = row["cn"]
    return lut


def load_custom(path):
    """Parse a user‐supplied CSV file into {(lc,hsg): cn}."""
    lut = {}
    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                lut[row["lc"], row["hsg"]] = row["cn"]
    except Exception as e:
        fatal(_("Unable to read lookup '{path}': {e}").format(path=path, e=e))
    if not lut:
        fatal(_("Custom lookup table is empty or malformed"))
    return lut


# nested if() expression for r.mapcalc
def build_expression(landmap, hsg, lut):
    expr = "null()"
    for (lc, grp), cn in reversed(list(lut.items())):
        # NOTE: use 'landmap' here, not 'landcover'
        expr = f"if({landmap}=={lc} && {hsg}=={grp}, {cn}, {expr})"
    return expr


# Main entry point
def main():
    opts, flags = parser()
    landmap = opts["landcover"]
    hsgmap = opts["soil"]
    source = opts["landcover_source"]
    custom = opts.get("lookup")
    outmap = opts["output"]

    if source and source.lower() == "nlcd":
        lut = parse_csv(NLCD_CSV)
    elif source and source.lower() == "esa":
        lut = parse_csv(ESA_CSV)
    elif custom:
        lut = load_custom(custom)
    else:
        fatal("Must specify --source=nlcd|esa or provide --lookup for custom")

    expr = build_expression(landmap, hsgmap, lut)
    run_command("r.mapcalc", expression=f"{outmap} = {expr}")


if __name__ == "__main__":
    main()
