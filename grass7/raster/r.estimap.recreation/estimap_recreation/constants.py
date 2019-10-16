"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

CITATION_RECREATION_POTENTIAL = "Zulian (2014)"
SPACY_PLUS = " + "
EQUATION = "{result} = {expression}"  # basic equation for mapcalc

THRESHHOLD_ZERO = 0
THRESHHOLD_0001 = 0.0001

COLUMN_PREFIX_SPECTRUM = 'spectrum'
COLUMN_PREFIX_UNMET = 'unmet'
COLUMN_PREFIX_DEMAND = 'demand'
COLUMN_PREFIX_UNMET = 'unmet'
COLUMN_PREFIX_FLOW = 'flow'

CSV_EXTENSION = ".csv"
COMMA = "comma"
METHODS = "sum"
EUCLIDEAN = "euclidean"
# units='k'
NEIGHBORHOOD_SIZE = 11  # this and below, required for neighborhood_function
NEIGHBORHOOD_METHOD = "mode"

WATER_PROXIMITY_CONSTANT = 1
WATER_PROXIMITY_KAPPA = 30
WATER_PROXIMITY_ALPHA = 0.008
WATER_PROXIMITY_SCORE = 1
BATHING_WATER_PROXIMITY_CONSTANT = 1
BATHING_WATER_PROXIMITY_KAPPA = 5
BATHING_WATER_PROXIMITY_ALPHA = 0.1101

SUITABILITY_SCORES = """
1:1:0:0
2:2:0.1:0.1
3:9:0:0
10:10:1:1
11:11:0.1:0.1
12:13:0.3:0.3
14:14:0.4:0.4
15:17:0.5:0.5
18:18:0.6:0.6
19:20:0.3:0.3
21:22:0.6:0.6
23:23:1:1
24:24:0.8:0.8
25:25:1:1
26:29:0.8:0.8
30:30:1:1
31:31:0.8:0.8
32:32:0.7:0.7
33:33:0:0
34:34:0.8:0.8
35:35:1:1
36:36:0.8:0.8
37:37:1:1
38:38:0.8:0.8
39:39:1:1
40:42:1:1
43:43:0.8:0.8
44:44:1:1
45:45:0.3:0.3
""".strip()

SUITABILITY_SCORES_LABELS = """
1 thru 1 = 1 0
2 thru 2 = 2 0.1
3 thru 9 = 9 0
10 thru 10 = 10 1
11 thru 11 = 11 0.1
12 thru 13 = 13 0.3
14 thru 14 = 14 0.4
15 thru 17 = 17 0.5
18 thru 18 = 18 0.6
19 thru 20 = 20 0.3
21 thru 22 = 22 0.6
23 thru 23 = 23 1
24 thru 24 = 24 0.8
25 thru 25 = 25 1
26 thru 29 = 29 0.8
30 thru 30 = 30 1
31 thru 31 = 31 0.8
32 thru 32 = 32 0.7
33 thru 33 = 33 0
34 thru 34 = 34 0.8
35 thru 35 = 35 1
36 thru 36 = 36 0.8
37 thru 37 = 37 1
38 thru 38 = 38 0.8
39 thru 39 = 39 1
40 thru 42 = 42 1
43 thru 43 = 43 0.8
44 thru 44 = 44 1
45 thru 45 = 45 0.3
""".strip()

URBAN_ATLAS_CATEGORIES = """
11100
11200
12100
12200
12300
12400
13100
13200
13300
14100
14200
21100
21200
21300
22100
22200
22300
23100
24100
24200
24300
24400
31100
31200
31300
32100
32200
32300
32400
33100
33200
33300
33400
33500
41100
41200
42100
42200
42300
""".strip()

URBAN_ATLAS_TO_MAES_NOMENCLATURE = """
11100 = 1 Urban
11210 = 1 Urban
11220 = 1 Urban
11230 = 1 Urban
11240 = 1 Urban
11300 = 1 Urban
12100 = 1 Urban
12210 = 1 Urban
12220 = 1 Urban
12230 = 1 Urban
12300 = 1 Urban
12400 = 1 Urban
13100 = 1 Urban
13300 = 1 Urban
13400 = 1 Urban
14100 = 1 Urban
14200 = 1 Urban
21000 = 2 Cropland
22000 = 2 Cropland
23000 = 2 Cropland
25400 = 2 Cropland
31000 = 3 Woodland and forest
32000 = 3 Woodland and forest
33000 = 3 Woodland and forest
40000 = 4 Grassland
50000 = 5 Heathland and shrub
""".strip()

# Recreation

RECREATION_POTENTIAL_CATEGORIES = """
0.0:0.2:1
0.2:0.4:2
0.4:*:3
""".strip()
# artificial_distance_categories=
#'0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5'
RECREATION_OPPORTUNITY_CATEGORIES = RECREATION_POTENTIAL_CATEGORIES
HIGHEST_RECREATION_CATEGORY = 9

# Mobility

MOBILITY_CONSTANT = 1
MOBILITY_COEFFICIENTS = {
    0: (0.02350, 0.00102),
    1: (0.02651, 0.00109),
    2: (0.05120, 0.00098),
    3: (0.10700, 0.00067),
    4: (0.06930, 0.00057),
}
MOBILITY_SCORE = 52
