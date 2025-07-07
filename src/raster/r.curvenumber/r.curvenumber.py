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
"""It generates the curve number raster based on the land cover, hydrologic soil group rasters, hydrologic condition, and antecedent runoff conditions"""

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
# % description: CSV with columns lc,hsg,hc,cn (required if source=custom)
# % required: no
# %end

# %option
# % key: hydrologic_condition
# % type: string
# % description: Hydrologic condition (groundcover density affecting runoff potential)
# % options: poor,fair,good
# % descriptions: poor;increased runoff;fair;normal runoff;good;lower runoff
# % answer: fair
# % required: no
# %end

# %option
# % key: antecedent_runoff_condition
# % type: string
# % description: Antecedent Runoff Condition (the degree of wetness of a watershed before a rainfall event)
# % options: i,ii,iii
# % descriptions: i;dry;ii;average;iii;wet
# % answer: ii
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % description: Curve number raster
# %end

import csv
from grass.script import parser, run_command, fatal, warning

# Embedded lookup tables for ARC ii only
NLCD_II_CSV = """lc,hsg,hc,cn
11,1,poor,100
11,2,poor,100
11,3,poor,100
11,4,poor,100
11,1,fair,100
11,2,fair,100
11,3,fair,100
11,4,fair,100
11,1,good,100
11,2,good,100
11,3,good,100
11,4,good,100
12,1,poor,0
12,2,poor,0
12,3,poor,0
12,4,poor,0
12,1,fair,0
12,2,fair,0
12,3,fair,0
12,4,fair,0
12,1,good,0
12,2,good,0
12,3,good,0
12,4,good,0
21,1,poor,68
21,2,poor,79
21,3,poor,86
21,4,poor,89
21,1,fair,49
21,2,fair,69
21,3,fair,79
21,4,fair,84
21,1,good,39
21,2,good,61
21,3,good,74
21,4,good,80
22,1,poor,74
22,2,poor,86
22,3,poor,90
22,4,poor,92
22,1,fair,64
22,2,fair,79
22,3,fair,86
22,4,fair,89
22,1,good,55
22,2,good,74
22,3,good,82
22,4,good,86
24,1,poor,98
24,2,poor,98
24,3,poor,98
24,4,poor,98
24,1,fair,97
24,2,fair,97
24,3,fair,97
24,4,fair,97
24,1,good,95
24,2,good,95
24,3,good,95
24,4,good,95
31,1,poor,82
31,2,poor,87
31,3,poor,91
31,4,poor,93
31,1,fair,55
31,2,fair,70
31,3,fair,80
31,4,fair,85
31,1,good,45
31,2,good,65
31,3,good,75
31,4,good,80
41,1,poor,45
41,2,poor,66
41,3,poor,77
41,4,poor,83
41,1,fair,35
41,2,fair,59
41,3,fair,72
41,4,fair,78
41,1,good,30
41,2,good,53
41,3,good,68
41,4,good,75
42,1,poor,47
42,2,poor,68
42,3,poor,79
42,4,poor,85
42,1,fair,37
42,2,fair,61
42,3,fair,74
42,4,fair,80
42,1,good,30
42,2,good,55
42,3,good,70
42,4,good,77
43,1,poor,46
43,2,poor,67
43,3,poor,78
43,4,poor,84
43,1,fair,36
43,2,fair,60
43,3,fair,73
43,4,fair,79
43,1,good,30
43,2,good,54
43,3,good,69
43,4,good,76
51,1,poor,46
51,2,poor,65
51,3,poor,75
51,4,poor,81
51,1,fair,33
51,2,fair,54
51,3,fair,68
51,4,fair,75
51,1,good,30
51,2,good,46
51,3,good,63
51,4,good,71
52,1,poor,48
52,2,poor,67
52,3,poor,77
52,4,poor,83
52,1,fair,35
52,2,fair,56
52,3,fair,70
52,4,fair,77
52,1,good,30
52,2,good,48
52,3,good,65
52,4,good,73
71,1,poor,68
71,2,poor,79
71,3,poor,86
71,4,poor,89
71,1,fair,49
71,2,fair,69
71,3,fair,79
71,4,fair,84
71,1,good,39
71,2,good,61
71,3,good,74
71,4,good,80
72,1,poor,60
72,2,poor,75
72,3,poor,82
72,4,poor,85
72,1,fair,45
72,2,fair,65
72,3,fair,75
72,4,fair,80
72,1,good,35
72,2,good,57
72,3,good,70
72,4,good,76
73,1,poor,55
73,2,poor,70
73,3,poor,80
73,4,poor,83
73,1,fair,40
73,2,fair,60
73,3,fair,72
73,4,fair,78
73,1,good,30
73,2,good,50
73,3,good,65
73,4,good,73
74,1,poor,53
74,2,poor,68
74,3,poor,78
74,4,poor,81
74,1,fair,38
74,2,fair,58
74,3,fair,70
74,4,fair,76
74,1,good,30
74,2,good,48
74,3,good,63
74,4,good,71
81,1,poor,68
81,2,poor,79
81,3,poor,86
81,4,poor,89
81,1,fair,49
81,2,fair,69
81,3,fair,79
81,4,fair,84
81,1,good,30
81,2,good,58
81,3,good,71
81,4,good,78
82,1,poor,57
82,2,poor,73
82,3,poor,82
82,4,poor,86
82,1,fair,43
82,2,fair,65
82,3,fair,76
82,4,fair,82
82,1,good,32
82,2,good,58
82,3,good,72
82,4,good,79
90,1,poor,40
90,2,poor,60
90,3,poor,72
90,4,poor,80
90,1,fair,32
90,2,fair,55
90,3,fair,68
90,4,fair,75
90,1,good,30
90,2,good,50
90,3,good,65
90,4,good,73
95,1,poor,60
95,2,poor,75
95,3,poor,82
95,4,poor,85
95,1,fair,45
95,2,fair,65
95,3,fair,75
95,4,fair,80
95,1,good,30
95,2,good,50
95,3,good,65
95,4,good,70
"""

ESA_II_CSV = """lc,hsg,hc,cn
10,1,poor,45
10,2,poor,66
10,3,poor,77
10,4,poor,83
10,1,fair,36
10,2,fair,60
10,3,fair,73
10,4,fair,79
10,1,good,30
10,2,good,55
10,3,good,70
10,4,good,77
20,1,poor,63
20,2,poor,77
20,3,poor,85
20,4,poor,88
20,1,fair,55
20,2,fair,72
20,3,fair,81
20,4,fair,86
20,1,good,49
20,2,good,68
20,3,good,79
20,4,good,84
30,1,poor,68
30,2,poor,79
30,3,poor,86
30,4,poor,89
30,1,fair,49
30,2,fair,69
30,3,fair,79
30,4,fair,84
30,1,good,39
30,2,good,61
30,3,good,74
30,4,good,80
40,1,poor,72
40,2,poor,81
40,3,poor,88
40,4,poor,91
40,1,fair,70
40,2,fair,80
40,3,fair,87
40,4,fair,90
40,1,good,67
40,2,good,78
40,3,good,85
40,4,good,89
50,1,poor,89
50,2,poor,92
50,3,poor,94
50,4,poor,95
50,1,fair,89
50,2,fair,92
50,3,fair,94
50,4,fair,95
50,1,good,89
50,2,good,92
50,3,good,94
50,4,good,95
60,1,poor,65
60,2,poor,79
60,3,poor,87
60,4,poor,90
60,1,fair,65
60,2,fair,79
60,3,fair,87
60,4,fair,90
60,1,good,65
60,2,good,79
60,3,good,87
60,4,good,90
70,1,poor,0
70,2,poor,0
70,3,poor,0
70,4,poor,0
70,1,fair,0
70,2,fair,0
70,3,fair,0
70,4,fair,0
70,1,good,0
70,2,good,0
70,3,good,0
70,4,good,0
80,1,poor,100
80,2,poor,100
80,3,poor,100
80,4,poor,100
80,1,fair,100
80,2,fair,100
80,3,fair,100
80,4,fair,100
80,1,good,100
80,2,good,100
80,3,good,100
80,4,good,100
90,1,poor,80
90,2,poor,80
90,3,poor,80
90,4,poor,80
90,1,fair,80
90,2,fair,80
90,3,fair,80
90,4,fair,80
90,1,good,80
90,2,good,80
90,3,good,80
90,4,good,80
95,1,poor,0
95,2,poor,0
95,3,poor,0
95,4,poor,0
95,1,fair,0
95,2,fair,0
95,3,fair,0
95,4,fair,0
95,1,good,0
95,2,good,0
95,3,good,0
95,4,good,0
100,1,poor,74
100,2,poor,77
100,3,poor,78
100,4,poor,79
100,1,fair,74
100,2,fair,77
100,3,fair,78
100,4,fair,79
100,1,good,74
100,2,good,77
100,3,good,78
100,4,good,79
"""

# ARC conversion table
ARC_CONVERSION_CSV = """arc_ii,arc_i,arc_iii
100,100,100
99,97,100
98,94,99
97,91,99
96,89,99
95,87,98
94,85,98
93,83,98
92,81,97
91,80,97
90,78,96
89,76,96
88,75,95
87,73,95
86,72,94
85,70,94
84,68,93
83,67,93
82,66,92
81,64,92
80,63,91
79,62,91
78,60,90
77,59,89
76,58,89
75,57,88
74,55,88
73,54,87
72,53,86
71,52,86
70,51,85
69,50,84
68,48,84
67,47,83
66,46,82
65,45,82
64,44,81
63,43,80
62,42,79
61,41,78
60,40,78
59,39,77
58,38,76
57,37,75
56,36,75
55,35,74
54,34,73
53,33,72
52,32,71
51,31,70
50,31,70
49,30,69
48,29,68
47,28,67
46,27,66
45,26,65
44,25,64
43,25,63
42,24,62
41,23,61
40,22,60
39,21,59
38,21,58
37,20,57
36,19,56
35,18,55
34,18,54
33,17,53
32,16,52
31,16,51
30,15,50
25,12,43
20,9,37
15,6,30
10,4,22
5,2,13
0,0,0
"""


# CSV parsing helpers
def parse_csv(text):
    """Parse an embedded CSV string into {(lc,hsg,hc): cn} for ARC ii tables."""
    lut = {}
    for row in csv.DictReader(text.strip().splitlines()):
        lut[row["lc"].lower(), row["hsg"].lower(), row["hc"].lower()] = row["cn"]
    return lut


def parse_conversion_csv(text):
    """Parse the ARC conversion CSV into {arc_ii: {arc: cn}}."""
    conv = {}
    for row in csv.DictReader(text.strip().splitlines()):
        arc_ii = int(row["arc_ii"])
        arc_i = int(row["arc_i"])
        arc_iii = int(row["arc_iii"])
        conv[arc_ii] = {"i": arc_i, "ii": arc_ii, "iii": arc_iii}
    return conv


def load_custom(path):
    """Parse a user-supplied CSV file into {(lc,hsg,hc): cn}."""
    lut = {}
    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                lut[
                    row["lc"].lower(),
                    row["hsg"].lower(),
                    row["hc"].lower(),
                ] = row["cn"]
    except Exception as e:
        fatal(_("Unable to read lookup '{path}': {e}").format(path=path, e=e))
    if not lut:
        fatal(_("Custom lookup table is empty or malformed"))
    return lut


# nested if() expression for r.mapcalc with ARC conversion
def build_expression(landmap, hsg, lut, conv, hc, arc):
    expr = "null()"
    for (lc, grp, hc_val), cn in reversed(list(lut.items())):
        if hc_val == hc:
            base_cn = int(cn)
            # dynamic ARC conversion
            adjusted_cn = (
                conv.get(base_cn, {}).get(arc, base_cn) if arc != "ii" else base_cn
            )
            expr = f"if({landmap}=={lc} && {hsg}=={grp}, {adjusted_cn}, {expr})"

    # enforce minimum CN of 30
    expr = f"if({expr} > 0 && {expr} < 30, 30, {expr})"
    return expr


def main():
    opts, flags = parser()
    landmap = opts["landcover"]
    hsgmap = opts["soil"]
    source = opts["landcover_source"].lower()
    custom = opts.get("lookup")
    hc = opts["hydrologic_condition"].lower()
    arc = opts["antecedent_runoff_condition"].lower()
    outmap = opts["output"]

    # load appropriate lookup table for ARC ii
    if source == "nlcd":
        lut = parse_csv(NLCD_II_CSV)
    elif source == "esa":
        lut = parse_csv(ESA_II_CSV)
    elif custom:
        lut = load_custom(custom)
    else:
        fatal(_("Must specify --source=nlcd|esa or provide lookup for custom"))

    # Load ARC conversion table
    conv = parse_conversion_csv(ARC_CONVERSION_CSV)

    expr = build_expression(landmap, hsgmap, lut, conv, hc, arc)
    run_command("r.mapcalc", expression=f"{outmap} = {expr}")


if __name__ == "__main__":
    main()
