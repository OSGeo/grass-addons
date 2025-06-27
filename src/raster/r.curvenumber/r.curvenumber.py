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
# % description: CSV with columns lc,hsg,hc,arc,cn (required if source=custom)
# % required: no
# %end

# %option
# % key: hydrologic_condition
# % type: string
# % description: Hydrologic condition
# % options: poor,fair,good
# % answer: fair
# % required: no
# %end

# %option
# % key: antecedent_runoff_condition
# % type: string
# % description: Antecedent Runoff Condition (ARC)
# % options: i,ii,iii
# % answer: ii
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % description: Curve number raster
# %end

import csv
from grass.script import parser, run_command, fatal, warning

# Embedded lookup tables
NLCD_CSV = """lc,hsg,hc,arc,cn
11,1,poor,i,100
11,2,poor,i,100
11,3,poor,i,100
11,4,poor,i,100
11,1,fair,i,100
11,2,fair,i,100
11,3,fair,i,100
11,4,fair,i,100
11,1,good,i,100
11,2,good,i,100
11,3,good,i,100
11,4,good,i,100
11,1,poor,ii,100
11,2,poor,ii,100
11,3,poor,ii,100
11,4,poor,ii,100
11,1,fair,ii,100
11,2,fair,ii,100
11,3,fair,ii,100
11,4,fair,ii,100
11,1,good,ii,100
11,2,good,ii,100
11,3,good,ii,100
11,4,good,ii,100
11,1,poor,iii,100
11,2,poor,iii,100
11,3,poor,iii,100
11,4,poor,iii,100
11,1,fair,iii,100
11,2,fair,iii,100
11,3,fair,iii,100
11,4,fair,iii,100
11,1,good,iii,100
11,2,good,iii,100
11,3,good,iii,100
11,4,good,iii,100
12,1,poor,i,0
12,2,poor,i,0
12,3,poor,i,0
12,4,poor,i,0
12,1,fair,i,0
12,2,fair,i,0
12,3,fair,i,0
12,4,fair,i,0
12,1,good,i,0
12,2,good,i,0
12,3,good,i,0
12,4,good,i,0
12,1,poor,ii,0
12,2,poor,ii,0
12,3,poor,ii,0
12,4,poor,ii,0
12,1,fair,ii,0
12,2,fair,ii,0
12,3,fair,ii,0
12,4,fair,ii,0
12,1,good,ii,0
12,2,good,ii,0
12,3,good,ii,0
12,4,good,ii,0
12,1,poor,iii,0
12,2,poor,iii,0
12,3,poor,iii,0
12,4,poor,iii,0
12,1,fair,iii,0
12,2,fair,iii,0
12,3,fair,iii,0
12,4,fair,iii,0
12,1,good,iii,0
12,2,good,iii,0
12,3,good,iii,0
12,4,good,iii,0
21,1,poor,i,48
21,2,poor,i,62
21,3,poor,i,72
21,4,poor,i,76
21,1,fair,i,30
21,2,fair,i,50
21,3,fair,i,62
21,4,fair,i,68
21,1,good,i,21
21,2,good,i,41
21,3,good,i,55
21,4,good,i,63
21,1,poor,ii,68
21,2,poor,ii,79
21,3,poor,ii,86
21,4,poor,ii,89
21,1,fair,ii,49
21,2,fair,ii,69
21,3,fair,ii,79
21,4,fair,ii,84
21,1,good,ii,39
21,2,good,ii,61
21,3,good,ii,74
21,4,good,ii,80
21,1,poor,iii,84
21,2,poor,iii,91
21,3,poor,iii,94
21,4,poor,iii,96
21,1,fair,iii,69
21,2,fair,iii,84
21,3,fair,iii,91
21,4,fair,iii,93
21,1,good,iii,59
21,2,good,iii,78
21,3,good,iii,88
21,4,good,iii,91
22,1,poor,i,55
22,2,poor,i,72
22,3,poor,i,78
22,4,poor,i,81
22,1,fair,i,44
22,2,fair,i,62
22,3,fair,i,72
22,4,fair,i,78
22,1,good,i,35
22,2,good,i,55
22,3,good,i,66
22,4,good,i,72
22,1,poor,ii,74
22,2,poor,ii,86
22,3,poor,ii,90
22,4,poor,ii,92
22,1,fair,ii,64
22,2,fair,ii,79
22,3,fair,ii,86
22,4,fair,ii,89
22,1,good,ii,55
22,2,good,ii,74
22,3,good,ii,82
22,4,good,ii,86
22,1,poor,iii,86
22,2,poor,iii,93
22,3,poor,iii,95
22,4,poor,iii,97
22,1,fair,iii,78
22,2,fair,iii,89
22,3,fair,iii,93
22,4,fair,iii,95
22,1,good,iii,70
22,2,good,iii,84
22,3,good,iii,90
22,4,good,iii,93
24,1,poor,i,94
24,2,poor,i,94
24,3,poor,i,94
24,4,poor,i,94
24,1,fair,i,91
24,2,fair,i,91
24,3,fair,i,91
24,4,fair,i,91
24,1,good,i,87
24,2,good,i,87
24,3,good,i,87
24,4,good,i,87
24,1,poor,ii,98
24,2,poor,ii,98
24,3,poor,ii,98
24,4,poor,ii,98
24,1,fair,ii,97
24,2,fair,ii,97
24,3,fair,ii,97
24,4,fair,ii,97
24,1,good,ii,95
24,2,good,ii,95
24,3,good,ii,95
24,4,good,ii,95
24,1,poor,iii,99
24,2,poor,iii,99
24,3,poor,iii,99
24,4,poor,iii,99
24,1,fair,iii,99
24,2,fair,iii,99
24,3,fair,iii,99
24,4,fair,iii,99
24,1,good,iii,98
24,2,good,iii,98
24,3,good,iii,98
24,4,good,iii,98
31,1,poor,i,66
31,2,poor,i,73
31,3,poor,i,80
31,4,poor,i,83
31,1,fair,i,35
31,2,fair,i,51
31,3,fair,i,63
31,4,fair,i,70
31,1,good,i,26
31,2,good,i,45
31,3,good,i,57
31,4,good,i,63
31,1,poor,ii,82
31,2,poor,ii,87
31,3,poor,ii,91
31,4,poor,ii,93
31,1,fair,ii,55
31,2,fair,ii,70
31,3,fair,ii,80
31,4,fair,ii,85
31,1,good,ii,45
31,2,good,ii,65
31,3,good,ii,75
31,4,good,ii,80
31,1,poor,iii,92
31,2,poor,iii,95
31,3,poor,iii,97
31,4,poor,iii,98
31,1,fair,iii,73
31,2,fair,iii,84
31,3,fair,iii,91
31,4,fair,iii,93
31,1,good,iii,59
31,2,good,iii,78
31,3,good,iii,88
31,4,good,iii,91
41,1,poor,i,26
41,2,poor,i,46
41,3,poor,i,59
41,4,poor,i,67
41,1,fair,i,18
41,2,fair,i,39
41,3,fair,i,53
41,4,fair,i,60
41,1,good,i,12
41,2,good,i,33
41,3,good,i,48
41,4,good,i,57
41,1,poor,ii,45
41,2,poor,ii,66
41,3,poor,ii,77
41,4,poor,ii,83
41,1,fair,ii,35
41,2,fair,ii,59
41,3,fair,ii,72
41,4,fair,ii,78
41,1,good,ii,25
41,2,good,ii,53
41,3,good,ii,68
41,4,good,ii,75
41,1,poor,iii,65
41,2,poor,iii,82
41,3,poor,iii,89
41,4,poor,iii,93
41,1,fair,iii,55
41,2,fair,iii,77
41,3,fair,iii,86
41,4,fair,iii,90
41,1,good,iii,43
41,2,good,iii,72
41,3,good,iii,84
41,4,good,iii,88
42,1,poor,i,28
42,2,poor,i,48
42,3,poor,i,62
42,4,poor,i,70
42,1,fair,i,20
42,2,fair,i,41
42,3,fair,i,55
42,4,fair,i,63
42,1,good,i,15
42,2,good,i,35
42,3,good,i,51
42,4,good,i,59
42,1,poor,ii,47
42,2,poor,ii,68
42,3,poor,ii,79
42,4,poor,ii,85
42,1,fair,ii,37
42,2,fair,ii,61
42,3,fair,ii,74
42,4,fair,ii,80
42,1,good,ii,30
42,2,good,ii,55
42,3,good,ii,70
42,4,good,ii,77
42,1,poor,iii,67
42,2,poor,iii,84
42,3,poor,iii,91
42,4,poor,iii,94
42,1,fair,iii,57
42,2,fair,iii,78
42,3,fair,iii,88
42,4,fair,iii,91
42,1,good,iii,50
42,2,good,iii,73
42,3,good,iii,85
42,4,good,iii,89
43,1,poor,i,27
43,2,poor,i,47
43,3,poor,i,60
43,4,poor,i,68
43,1,fair,i,19
43,2,fair,i,40
43,3,fair,i,54
43,4,fair,i,62
43,1,good,i,12
43,2,good,i,34
43,3,good,i,50
43,4,good,i,58
43,1,poor,ii,46
43,2,poor,ii,67
43,3,poor,ii,78
43,4,poor,ii,84
43,1,fair,ii,36
43,2,fair,ii,60
43,3,fair,ii,73
43,4,fair,ii,79
43,1,good,ii,25
43,2,good,ii,54
43,3,good,ii,69
43,4,good,ii,76
43,1,poor,iii,66
43,2,poor,iii,83
43,3,poor,iii,90
43,4,poor,iii,93
43,1,fair,iii,56
43,2,fair,iii,78
43,3,fair,iii,87
43,4,fair,iii,91
43,1,good,iii,43
43,2,good,iii,73
43,3,good,iii,84
43,4,good,iii,89
51,1,poor,i,27
51,2,poor,i,45
51,3,poor,i,57
51,4,poor,i,64
51,1,fair,i,17
51,2,fair,i,34
51,3,fair,i,48
51,4,fair,i,57
51,1,good,i,12
51,2,good,i,27
51,3,good,i,43
51,4,good,i,52
51,1,poor,ii,46
51,2,poor,ii,65
51,3,poor,ii,75
51,4,poor,ii,81
51,1,fair,ii,33
51,2,fair,ii,54
51,3,fair,ii,68
51,4,fair,ii,75
51,1,good,ii,25
51,2,good,ii,46
51,3,good,ii,63
51,4,good,ii,71
51,1,poor,iii,66
51,2,poor,iii,82
51,3,poor,iii,88
51,4,poor,iii,92
51,1,fair,iii,53
51,2,fair,iii,73
51,3,fair,iii,84
51,4,fair,iii,88
51,1,good,iii,43
51,2,good,iii,66
51,3,good,iii,80
51,4,good,iii,86
52,1,poor,i,29
52,2,poor,i,47
52,3,poor,i,59
52,4,poor,i,67
52,1,fair,i,18
52,2,fair,i,36
52,3,fair,i,51
52,4,fair,i,59
52,1,good,i,15
52,2,good,i,29
52,3,good,i,45
52,4,good,i,54
52,1,poor,ii,48
52,2,poor,ii,67
52,3,poor,ii,77
52,4,poor,ii,83
52,1,fair,ii,35
52,2,fair,ii,56
52,3,fair,ii,70
52,4,fair,ii,77
52,1,good,ii,30
52,2,good,ii,48
52,3,good,ii,65
52,4,good,ii,73
52,1,poor,iii,68
52,2,poor,iii,83
52,3,poor,iii,89
52,4,poor,iii,93
52,1,fair,iii,55
52,2,fair,iii,74
52,3,fair,iii,85
52,4,fair,iii,89
52,1,good,iii,50
52,2,good,iii,68
52,3,good,iii,82
52,4,good,iii,87
71,1,poor,i,48
71,2,poor,i,62
71,3,poor,i,72
71,4,poor,i,76
71,1,fair,i,30
71,2,fair,i,50
71,3,fair,i,62
71,4,fair,i,68
71,1,good,i,21
71,2,good,i,41
71,3,good,i,55
71,4,good,i,63
71,1,poor,ii,68
71,2,poor,ii,79
71,3,poor,ii,86
71,4,poor,ii,89
71,1,fair,ii,49
71,2,fair,ii,69
71,3,fair,ii,79
71,4,fair,ii,84
71,1,good,ii,39
71,2,good,ii,61
71,3,good,ii,74
71,4,good,ii,80
71,1,poor,iii,84
71,2,poor,iii,91
71,3,poor,iii,94
71,4,poor,iii,96
71,1,fair,iii,69
71,2,fair,iii,84
71,3,fair,iii,91
71,4,fair,iii,93
71,1,good,iii,59
71,2,good,iii,78
71,3,good,iii,88
71,4,good,iii,91
72,1,poor,i,40
72,2,poor,i,57
72,3,poor,i,66
72,4,poor,i,70
72,1,fair,i,26
72,2,fair,i,45
72,3,fair,i,57
72,4,fair,i,63
72,1,good,i,18
72,2,good,i,37
72,3,good,i,51
72,4,good,i,58
72,1,poor,ii,60
72,2,poor,ii,75
72,3,poor,ii,82
72,4,poor,ii,85
72,1,fair,ii,45
72,2,fair,ii,65
72,3,fair,ii,75
72,4,fair,ii,80
72,1,good,ii,35
72,2,good,ii,57
72,3,good,ii,70
72,4,good,ii,76
72,1,poor,iii,78
72,2,poor,iii,88
72,3,poor,iii,92
72,4,poor,iii,94
72,1,fair,iii,65
72,2,fair,iii,82
72,3,fair,iii,88
72,4,fair,iii,91
72,1,good,iii,55
72,2,good,iii,75
72,3,good,iii,85
72,4,good,iii,89
73,1,poor,i,35
73,2,poor,i,51
73,3,poor,i,63
73,4,poor,i,67
73,1,fair,i,22
73,2,fair,i,40
73,3,fair,i,53
73,4,fair,i,60
73,1,good,i,15
73,2,good,i,31
73,3,good,i,45
73,4,good,i,54
73,1,poor,ii,55
73,2,poor,ii,70
73,3,poor,ii,80
73,4,poor,ii,83
73,1,fair,ii,40
73,2,fair,ii,60
73,3,fair,ii,72
73,4,fair,ii,78
73,1,good,ii,30
73,2,good,ii,50
73,3,good,ii,65
73,4,good,ii,73
73,1,poor,iii,73
73,2,poor,iii,85
73,3,poor,iii,91
73,4,poor,iii,93
73,1,fair,iii,60
73,2,fair,iii,78
73,3,fair,iii,86
73,4,fair,iii,90
73,1,good,iii,50
73,2,good,iii,70
73,3,good,iii,82
73,4,good,iii,87
74,1,poor,i,33
74,2,poor,i,48
74,3,poor,i,60
74,4,poor,i,64
74,1,fair,i,21
74,2,fair,i,38
74,3,fair,i,51
74,4,fair,i,58
74,1,good,i,12
74,2,good,i,29
74,3,good,i,43
74,4,good,i,52
74,1,poor,ii,53
74,2,poor,ii,68
74,3,poor,ii,78
74,4,poor,ii,81
74,1,fair,ii,38
74,2,fair,ii,58
74,3,fair,ii,70
74,4,fair,ii,76
74,1,good,ii,25
74,2,good,ii,48
74,3,good,ii,63
74,4,good,ii,71
74,1,poor,iii,72
74,2,poor,iii,84
74,3,poor,iii,90
74,4,poor,iii,92
74,1,fair,iii,58
74,2,fair,iii,76
74,3,fair,iii,85
74,4,fair,iii,89
74,1,good,iii,43
74,2,good,iii,68
74,3,good,iii,80
74,4,good,iii,86
81,1,poor,i,48
81,2,poor,i,62
81,3,poor,i,72
81,4,poor,i,76
81,1,fair,i,30
81,2,fair,i,50
81,3,fair,i,62
81,4,fair,i,68
81,1,good,i,15
81,2,good,i,38
81,3,good,i,52
81,4,good,i,60
81,1,poor,ii,68
81,2,poor,ii,79
81,3,poor,ii,86
81,4,poor,ii,89
81,1,fair,ii,49
81,2,fair,ii,69
81,3,fair,ii,79
81,4,fair,ii,84
81,1,good,ii,30
81,2,good,ii,58
81,3,good,ii,71
81,4,good,ii,78
81,1,poor,iii,84
81,2,poor,iii,91
81,3,poor,iii,94
81,4,poor,iii,96
81,1,fair,iii,69
81,2,fair,iii,84
81,3,fair,iii,91
81,4,fair,iii,93
81,1,good,iii,50
81,2,good,iii,76
81,3,good,iii,86
81,4,good,iii,90
82,1,poor,i,37
82,2,poor,i,54
82,3,poor,i,66
82,4,poor,i,72
82,1,fair,i,25
82,2,fair,i,45
82,3,fair,i,58
82,4,fair,i,66
82,1,good,i,16
82,2,good,i,38
82,3,good,i,53
82,4,good,i,62
82,1,poor,ii,57
82,2,poor,ii,73
82,3,poor,ii,82
82,4,poor,ii,86
82,1,fair,ii,43
82,2,fair,ii,65
82,3,fair,ii,76
82,4,fair,ii,82
82,1,good,ii,32
82,2,good,ii,58
82,3,good,ii,72
82,4,good,ii,79
82,1,poor,iii,75
82,2,poor,iii,87
82,3,poor,iii,92
82,4,poor,iii,94
82,1,fair,iii,63
82,2,fair,iii,82
82,3,fair,iii,89
82,4,fair,iii,92
82,1,good,iii,52
82,2,good,iii,76
82,3,good,iii,86
82,4,good,iii,91
90,1,poor,i,22
90,2,poor,i,40
90,3,poor,i,53
90,4,poor,i,63
90,1,fair,i,16
90,2,fair,i,35
90,3,fair,i,48
90,4,fair,i,57
90,1,good,i,12
90,2,good,i,31
90,3,good,i,45
90,4,good,i,54
90,1,poor,ii,40
90,2,poor,ii,60
90,3,poor,ii,72
90,4,poor,ii,80
90,1,fair,ii,32
90,2,fair,ii,55
90,3,fair,ii,68
90,4,fair,ii,75
90,1,good,ii,25
90,2,good,ii,50
90,3,good,ii,65
90,4,good,ii,73
90,1,poor,iii,60
90,2,poor,iii,78
90,3,poor,iii,86
90,4,poor,iii,91
90,1,fair,iii,52
90,2,fair,iii,73
90,3,fair,iii,84
90,4,fair,iii,88
90,1,good,iii,43
90,2,good,iii,70
90,3,good,iii,82
90,4,good,iii,87
95,1,poor,i,40
95,2,poor,i,57
95,3,poor,i,66
95,4,poor,i,70
95,1,fair,i,26
95,2,fair,i,45
95,3,fair,i,57
95,4,fair,i,63
95,1,good,i,12
95,2,good,i,31
95,3,good,i,45
95,4,good,i,51
95,1,poor,ii,60
95,2,poor,ii,75
95,3,poor,ii,82
95,4,poor,ii,85
95,1,fair,ii,45
95,2,fair,ii,65
95,3,fair,ii,75
95,4,fair,ii,80
95,1,good,ii,25
95,2,good,ii,50
95,3,good,ii,65
95,4,good,ii,70
95,1,poor,iii,78
95,2,poor,iii,88
95,3,poor,iii,92
95,4,poor,iii,94
95,1,fair,iii,65
95,2,fair,iii,82
95,3,fair,iii,88
95,4,fair,iii,91
95,1,good,iii,43
95,2,good,iii,70
95,3,good,iii,82
95,4,good,iii,85
"""

ESA_CSV = """lc,hsg,hc,arc,cn
10,1,poor,i,45
10,2,poor,i,66
10,3,poor,i,77
10,4,poor,i,83
10,1,poor,ii,26
10,2,poor,ii,46
10,3,poor,ii,59
10,4,poor,ii,67
10,1,poor,iii,65
10,2,poor,iii,82
10,3,poor,iii,89
10,4,poor,iii,93
10,1,fair,i,36
10,2,fair,i,60
10,3,fair,i,73
10,4,fair,i,79
10,1,fair,ii,19
10,2,fair,ii,40
10,3,fair,ii,54
10,4,fair,ii,62
10,1,fair,iii,56
10,2,fair,iii,78
10,3,fair,iii,87
10,4,fair,iii,91
10,1,good,i,30
10,2,good,i,55
10,3,good,i,70
10,4,good,i,77
10,1,good,ii,15
10,2,good,ii,35
10,3,good,ii,51
10,4,good,ii,59
10,1,good,iii,50
10,2,good,iii,74
10,3,good,iii,85
10,4,good,iii,89
20,1,poor,i,63
20,2,poor,i,77
20,3,poor,i,85
20,4,poor,i,88
20,1,poor,ii,43
20,2,poor,ii,59
20,3,poor,ii,70
20,4,poor,ii,75
20,1,poor,iii,80
20,2,poor,iii,89
20,3,poor,iii,94
20,4,poor,iii,95
20,1,fair,i,55
20,2,fair,i,72
20,3,fair,i,81
20,4,fair,i,86
20,1,fair,ii,35
20,2,fair,ii,53
20,3,fair,ii,64
20,4,fair,ii,72
20,1,fair,iii,74
20,2,fair,iii,86
20,3,fair,iii,92
20,4,fair,iii,94
20,1,good,i,49
20,2,good,i,68
20,3,good,i,79
20,4,good,i,84
20,1,good,ii,30
20,2,good,ii,48
20,3,good,ii,62
20,4,good,ii,68
20,1,good,iii,69
20,2,good,iii,84
20,3,good,iii,91
20,4,good,iii,93
30,1,poor,i,68
30,2,poor,i,79
30,3,poor,i,86
30,4,poor,i,89
30,1,poor,ii,48
30,2,poor,ii,62
30,3,poor,ii,72
30,4,poor,ii,76
30,1,poor,iii,84
30,2,poor,iii,91
30,3,poor,iii,94
30,4,poor,iii,96
30,1,fair,i,49
30,2,fair,i,69
30,3,fair,i,79
30,4,fair,i,84
30,1,fair,ii,30
30,2,fair,ii,50
30,3,fair,ii,62
30,4,fair,ii,68
30,1,fair,iii,69
30,2,fair,iii,84
30,3,fair,iii,91
30,4,fair,iii,93
30,1,good,i,39
30,2,good,i,61
30,3,good,i,74
30,4,good,i,80
30,1,good,ii,21
30,2,good,ii,41
30,3,good,ii,55
30,4,good,ii,63
30,1,good,iii,59
30,2,good,iii,78
30,3,good,iii,88
30,4,good,iii,91
40,1,poor,i,72
40,2,poor,i,81
40,3,poor,i,88
40,4,poor,i,91
40,1,poor,ii,53
40,2,poor,ii,64
40,3,poor,ii,75
40,4,poor,ii,80
40,1,poor,iii,86
40,2,poor,iii,92
40,3,poor,iii,95
40,4,poor,iii,97
40,1,fair,i,0
40,2,fair,i,0
40,3,fair,i,0
40,4,fair,i,0
40,1,fair,ii,0
40,2,fair,ii,0
40,3,fair,ii,0
40,4,fair,ii,0
40,1,fair,iii,0
40,2,fair,iii,0
40,3,fair,iii,0
40,4,fair,iii,0
40,1,good,i,67
40,2,good,i,78
40,3,good,i,85
40,4,good,i,89
40,1,good,ii,47
40,2,good,ii,60
40,3,good,ii,70
40,4,good,ii,76
40,1,good,iii,83
40,2,good,iii,90
40,3,good,iii,94
40,4,good,iii,96
50,1,poor,i,89
50,2,poor,i,92
50,3,poor,i,94
50,4,poor,i,95
50,1,poor,ii,76
50,2,poor,ii,81
50,3,poor,ii,85
50,4,poor,ii,87
50,1,poor,iii,96
50,2,poor,iii,97
50,3,poor,iii,98
50,4,poor,iii,98
50,1,fair,i,89
50,2,fair,i,92
50,3,fair,i,94
50,4,fair,i,95
50,1,fair,ii,76
50,2,fair,ii,81
50,3,fair,ii,85
50,4,fair,ii,87
50,1,fair,iii,96
50,2,fair,iii,97
50,3,fair,iii,98
50,4,fair,iii,98
50,1,good,i,89
50,2,good,i,92
50,3,good,i,94
50,4,good,i,95
50,1,good,ii,76
50,2,good,ii,81
50,3,good,ii,85
50,4,good,ii,87
50,1,good,iii,96
50,2,good,iii,97
50,3,good,iii,98
50,4,good,iii,98
60,1,poor,i,65
60,2,poor,i,79
60,3,poor,i,87
60,4,poor,i,90
60,1,poor,ii,45
60,2,poor,ii,62
60,3,poor,ii,73
60,4,poor,ii,78
60,1,poor,iii,82
60,2,poor,iii,91
60,3,poor,iii,95
60,4,poor,iii,96
60,1,fair,i,65
60,2,fair,i,79
60,3,fair,i,87
60,4,fair,i,90
60,1,fair,ii,45
60,2,fair,ii,62
60,3,fair,ii,73
60,4,fair,ii,78
60,1,fair,iii,82
60,2,fair,iii,91
60,3,fair,iii,95
60,4,fair,iii,96
60,1,good,i,65
60,2,good,i,79
60,3,good,i,87
60,4,good,i,90
60,1,good,ii,45
60,2,good,ii,62
60,3,good,ii,73
60,4,good,ii,78
60,1,good,iii,82
60,2,good,iii,91
60,3,good,iii,95
60,4,good,iii,96
70,1,poor,i,0
70,2,poor,i,0
70,3,poor,i,0
70,4,poor,i,0
70,1,poor,ii,0
70,2,poor,ii,0
70,3,poor,ii,0
70,4,poor,ii,0
70,1,poor,iii,0
70,2,poor,iii,0
70,3,poor,iii,0
70,4,poor,iii,0
70,1,fair,i,0
70,2,fair,i,0
70,3,fair,i,0
70,4,fair,i,0
70,1,fair,ii,0
70,2,fair,ii,0
70,3,fair,ii,0
70,4,fair,ii,0
70,1,fair,iii,0
70,2,fair,iii,0
70,3,fair,iii,0
70,4,fair,iii,0
70,1,good,i,0
70,2,good,i,0
70,3,good,i,0
70,4,good,i,0
70,1,good,ii,0
70,2,good,ii,0
70,3,good,ii,0
70,4,good,ii,0
70,1,good,iii,0
70,2,good,iii,0
70,3,good,iii,0
70,4,good,iii,0
80,1,poor,i,100
80,2,poor,i,100
80,3,poor,i,100
80,4,poor,i,100
80,1,poor,ii,100
80,2,poor,ii,100
80,3,poor,ii,100
80,4,poor,ii,100
80,1,poor,iii,100
80,2,poor,iii,100
80,3,poor,iii,100
80,4,poor,iii,100
80,1,fair,i,100
80,2,fair,i,100
80,3,fair,i,100
80,4,fair,i,100
80,1,fair,ii,100
80,2,fair,ii,100
80,3,fair,ii,100
80,4,fair,ii,100
80,1,fair,iii,100
80,2,fair,iii,100
80,3,fair,iii,100
80,4,fair,iii,100
80,1,good,i,100
80,2,good,i,100
80,3,good,i,100
80,4,good,i,100
80,1,good,ii,100
80,2,good,ii,100
80,3,good,ii,100
80,4,good,ii,100
80,1,good,iii,100
80,2,good,iii,100
80,3,good,iii,100
80,4,good,iii,100
90,1,poor,i,80
90,2,poor,i,80
90,3,poor,i,80
90,4,poor,i,80
90,1,poor,ii,63
90,2,poor,ii,63
90,3,poor,ii,63
90,4,poor,ii,63
90,1,poor,iii,91
90,2,poor,iii,91
90,3,poor,iii,91
90,4,poor,iii,91
90,1,fair,i,80
90,2,fair,i,80
90,3,fair,i,80
90,4,fair,i,80
90,1,fair,ii,63
90,2,fair,ii,63
90,3,fair,ii,63
90,4,fair,ii,63
90,1,fair,iii,91
90,2,fair,iii,91
90,3,fair,iii,91
90,4,fair,iii,91
90,1,good,i,80
90,2,good,i,80
90,3,good,i,80
90,4,good,i,80
90,1,good,ii,63
90,2,good,ii,63
90,3,good,ii,63
90,4,good,ii,63
90,1,good,iii,91
90,2,good,iii,91
90,3,good,iii,91
90,4,good,iii,91
95,1,poor,i,0
95,2,poor,i,0
95,3,poor,i,0
95,4,poor,i,0
95,1,poor,ii,0
95,2,poor,ii,0
95,3,poor,ii,0
95,4,poor,ii,0
95,1,poor,iii,0
95,2,poor,iii,0
95,3,poor,iii,0
95,4,poor,iii,0
95,1,fair,i,0
95,2,fair,i,0
95,3,fair,i,0
95,4,fair,i,0
95,1,fair,ii,0
95,2,fair,ii,0
95,3,fair,ii,0
95,4,fair,ii,0
95,1,fair,iii,0
95,2,fair,iii,0
95,3,fair,iii,0
95,4,fair,iii,0
95,1,good,i,0
95,2,good,i,0
95,3,good,i,0
95,4,good,i,0
95,1,good,ii,0
95,2,good,ii,0
95,3,good,ii,0
95,4,good,ii,0
95,1,good,iii,0
95,2,good,iii,0
95,3,good,iii,0
95,4,good,iii,0
100,1,poor,i,74
100,2,poor,i,77
100,3,poor,i,78
100,4,poor,i,79
100,1,poor,ii,55
100,2,poor,ii,59
100,3,poor,ii,60
100,4,poor,ii,62
100,1,poor,iii,88
100,2,poor,iii,89
100,3,poor,iii,90
100,4,poor,iii,91
100,1,fair,i,74
100,2,fair,i,77
100,3,fair,i,78
100,4,fair,i,79
100,1,fair,ii,55
100,2,fair,ii,59
100,3,fair,ii,60
100,4,fair,ii,62
100,1,fair,iii,88
100,2,fair,iii,89
100,3,fair,iii,90
100,4,fair,iii,91
100,1,good,i,74
100,2,good,i,77
100,3,good,i,78
100,4,good,i,79
100,1,good,ii,55
100,2,good,ii,59
100,3,good,ii,60
100,4,good,ii,62
100,1,good,iii,88
100,2,good,iii,89
100,3,good,iii,90
100,4,good,iii,91
"""

# CSV parsing helpers
def parse_csv(text):
    """Parse an embedded CSV string into {(lc,hsg,hc,arc): cn}."""
    lut = {}
    for row in csv.DictReader(text.strip().splitlines()):
        lut[row["lc"].lower(), row["hsg"].lower(), row["hc"].lower(), row["arc"].lower()] = row["cn"]
        #lut[row["lc"], row["hsg"]] = row["cn"]
    return lut


def load_custom(path):
    """Parse a user‐supplied CSV file into {(lc,hsg,hc,arc): cn}."""
    lut = {}
    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                lut[row["lc"].lower(), row["hsg"].lower(), row["hc"].lower(), row["arc"].lower()] = row["cn"]
               # lut[row["lc"], row["hsg"]] = row["cn"]
    except Exception as e:
        fatal(_("Unable to read lookup '{path}': {e}").format(path=path, e=e))
    if not lut:
        fatal(_("Custom lookup table is empty or malformed"))
    return lut


# nested if() expression for r.mapcalc
def build_expression(landmap, hsg, lut, hc, arc):
    expr = "null()"
    for (lc, grp, hc_val, arc_val), cn in reversed(list(lut.items())):
        if hc_val == hc and arc_val == arc:
            # NOTE: use 'landmap' here, not 'landcover'
            expr = f"if({landmap}=={lc} && {hsg}=={grp}, {cn}, {expr})"
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

    if source == "nlcd":
        lut = parse_csv(NLCD_CSV)
    elif source == "esa":
        lut = parse_csv(ESA_CSV)
        if hc == "fair" and ("40", "A", "fair", arc) in lut and lut[("40", "A", "fair", arc)] == "0":
            warning(_("CN values for ESA cropland (lc=40) in fair condition are interpolated as the average of poor and good conditions"))
    elif custom:
        lut = load_custom(custom)
    else:
        fatal(_("Must specify --source=nlcd|esa or provide --lookup for custom"))

    expr = build_expression(landmap, hsgmap, lut, hc, arc)
    run_command("r.mapcalc", expression=f"{outmap} = {expr}")


if __name__ == "__main__":
    main()

