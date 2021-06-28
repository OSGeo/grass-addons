"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

MOBILITY_COLORS = "wave"
LANDCOVER_FRACTIONS_COLOR = "wave"

SCORE_COLORS = """
# http://colorbrewer2.org/?type=diverging&scheme=RdYlGn&n=11
0.0% 165:0:38
10.0% 215:48:39
20.0% 244:109:67
30.0% 253:174:97
40.0% 254:224:139
50.0% 255:255:191
60.0% 217:239:139
70.0% 166:217:106
80.0% 102:189:99
90.0% 26:152:80
100.0% 0:104:55
""".strip()

POTENTIAL_COLORS = """
# Cubehelix color table generated using:
#   r.colors.cubehelix -dn ncolors=3 map=recreation_potential nrotations=0.33 gamma=1.5 hue=0.9 dark=0.3 output=recreation_potential.colors
0.000% 55:29:66
33.333% 55:29:66
33.333% 157:85:132
66.667% 157:85:132
66.667% 235:184:193
100.000% 235:184:193
""".strip()

OPPORTUNITY_COLORS = """
# Cubehelix color table generated using:
#   r.colors.cubehelix -dn ncolors=3 map=recreation_potential nrotations=0.33 gamma=1.5 hue=0.9 dark=0.3 output=recreation_potential.colors
0.000% 55:29:66
33.333% 55:29:66
33.333% 157:85:132
66.667% 157:85:132
66.667% 235:184:193
100.000% 235:184:193
""".strip()

SPECTRUM_COLORS = """
# Cubehelix color table generated using:
#   r.colors.cubehelix -dn ncolors=9 map=recreation_spectrum nrotations=0.33 gamma=1.5 hue=0.9 dark=0.3 output=recreation_spectrum.colors
0.000% 55:29:66
11.111% 55:29:66
11.111% 79:40:85
22.222% 79:40:85
22.222% 104:52:102
33.333% 104:52:102
33.333% 131:67:118
44.444% 131:67:118
44.444% 157:85:132
55.556% 157:85:132
55.556% 180:104:145
66.667% 180:104:145
66.667% 202:128:159
77.778% 202:128:159
77.778% 221:156:175
88.889% 221:156:175
88.889% 235:184:193
100.000% 235:184:193
""".strip()
