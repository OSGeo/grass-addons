#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 MODULE:       r.estimap.recreation

 AUTHOR(S):    Nikos Alexandris <nik@nikosalexandris.net>

               First implementation as a collection of Python scripts by
               Grazia Zulian <Grazia.Zulian@ec.europa.eu>

 PURPOSE:      An implementation of the Ecosystem Services Mapping Tool
               (ESTIMAP). ESTIMAP is a collection of spatially explicit models
               to support mapping and modelling of ecosystem services
               at European scale.

 SOURCES:      https://www.bts.gov/archive/publications/journal_of_transportation_and_statistics/volume_04_number_23/paper_03/index

 COPYRIGHT:    Copyright 2018 European Union

               Licensed under the EUPL, Version 1.2 or – as soon they will be
               approved by the European Commission – subsequent versions of the
               EUPL (the "Licence");

               You may not use this work except in compliance with the Licence.
               You may obtain a copy of the Licence at:

               https://joinup.ec.europa.eu/collection/eupl/eupl-text-11-12

               Unless required by applicable law or agreed to in writing,
               software distributed under the Licence is distributed on an
               "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
               either express or implied. See the Licence for the specific
               language governing permissions and limitations under the Licence.

               Consult the LICENCE file for details.
"""

'''Flags'''

#%Module
#%  description: Implementation of ESTIMAP to support mapping and modelling of ecosystem services (Zulian, 2014)
#%  keywords: estimap
#%  keywords: ecosystem services
#%  keywords: recreation potential
#%End

#%flag
#%  key: e
#%  description: Match computational region to extent of land use map
#%end

#%flag
#%  key: f
#%  description: Filter maps in land and natural components before computing recreation maps
#%end

#%flag
#%  key: d
#%  description: Draw maps in terminology (developper's version)
#%end

#%flag
#%  key: s
#%  description: Save temporary maps for debugging
#%end

#%flag
#%  key: i
#%  description: Print out citation and other information
#%end

#%flag
#%  key: p
#%  description: Print out results (i.e. supply table), don't export to file
#%end

'''
exclusive: at most one of the options may be given
required: at least one of the options must be given
requires: if the first option is given, at least one of the subsequent options must also be given
requires_all: if the first option is given, all of the subsequent options must also be given
excludes: if the first option is given, none of the subsequent options may be given
collective: all or nothing; if any option is given, all must be given
'''

'''Components section'''

#%option G_OPT_R_INPUT
#% key: land
#% type: string
#% key_desc: name
#% label: Input map scoring access to and suitability of land resources for recreation
#% description: Arbitrary number of maps scoring access to and land resources suitability of land use classes to support recreation activities
#% required : no
#% guisection: Components
#%end

#%option G_OPT_R_INPUTS
#% key: natural
#% key_desc: name
#% label: Input maps scoring access to and quality of inland natural resources
#% description: Arbitrary number of maps scoring access to and quality of inland natural resources
#% required : no
#% guisection: Components
#%end

#%option G_OPT_R_INPUTS
#% key: water
#% key_desc: name
#% label: Input maps scoring access to and quality of water resources
#% description: Arbitrary number of maps scoring access to and quality of water resources such as lakes, sea, bathing waters and riparian zones
#% required : no
#% guisection: Components
#%end

#%option G_OPT_R_INPUTS
#% key: urban
#% key_desc: name
#% description: Input maps scoring recreational value of urban surfaces
#% required : no
#% guisection: Components
#%end

#%option G_OPT_R_INPUTS
#% key: infrastructure
#% type: string
#% key_desc: name
#% label: Input maps scoring infrastructure to reach locations of recreation activities
#% description: Infrastructure to reach locations of recreation activities [required to derive recreation spectrum map]
#% required: no
#% guisection: Components
#%end

#%option G_OPT_R_INPUTS
#% key: recreation
#% type: string
#% key_desc: name
#% label: Input maps scoring recreational facilities, amenities and services
#% description: Recreational opportunities facilities, amenities and services [required to derive recreation spectrum map]
#% required: no
#% guisection: Components
#%end

'''Land'''

#%option G_OPT_R_INPUT
#% key: landuse
#% type: string
#% key_desc: name
#% label: Input land features map from which to derive suitability for recreation
#% description: Input to derive suitability of land use classes to support recreation activities. Requires scores, overrides suitability.
#% required : no
#% guisection: Land
#%end

#%rules
#%  exclusive: land
#%end

#%option G_OPT_F_INPUT
#% key: suitability_scores
#% type: string
#% key_desc: filename
#% label: Input recreational suitability scores for the categories of the 'landuse' map
#% description: Scores for suitability of land to support recreation activities. Expected are rules for `r.recode` that correspond to categories of the input 'landuse' map. If the 'landuse' map is given and 'suitability_scores not provided, the module will use internal rules for the CORINE land classes.
#% required: no
#% guisection: Land
#%end

#%rules
#%  excludes: land, suitability_scores
#%end

#%option G_OPT_R_INPUT
#% key: landcover
#% type: string
#% key_desc: name
#% label: Input land cover map from which to derive cover percentages within zones of high recreational value
#% description: Input to derive percentage of land classes within zones of high recreational value.
#% required : no
#% guisection: Land
#%end

#%option G_OPT_F_INPUT
#% key: land_classes
#% type: string
#% key_desc: filename
#% label: Input reclassification rules for the classes of the 'landcover' map
#% description: Expected are rules for `r.reclass` that correspond to classes of the input 'landcover' map. If 'landcover' map is given and 'land_classess' not provided, the module will use internal rules for the Urban Atlas land classes
#% required: no
#% guisection: Land
#%end

'''Water'''

#%option G_OPT_R_INPUT
#% key: lakes
#% key_desc: name
#% label: Input map of inland waters resources for which to score accessibility
#% description: Map of inland water resources to compute proximity for, score accessibility based on a distance function
#% required : no
#% guisection: Water
#%end

#%option
#% key: lakes_coefficients
#% type: string
#% key_desc: Coefficients
#% label: Input distance function coefficients for the 'lakes' map
#% description: Distance function coefficients to compute proximity: distance metric, constant, kappa, alpha and score. Refer to the manual for details.
#% multiple: yes
#% required: no
#% guisection: Water
#% answer: euclidean,1,30,0.008,1
#%end

##%rules
##%  requires: lakes, lakes_coefficients
##%end

#%option G_OPT_R_INPUT
#% key: coastline
#% key_desc: name
#% label: Input sea coast map for which to compute proximity
#% description: Input map to compute coast proximity, scored based on a distance function
#% required : no
#% guisection: Water
#%end

#%option
#% key: coastline_coefficients
#% key_desc: Coefficients
#% label: Input distance function coefficients for the 'coastline' map
#% description: Distance function coefficients to compute proximity: distance metric, constant, kappa, alpha and score. Refer to the manual for details.
#% multiple: yes
#% required: no
#% guisection: Water
#% answer: euclidean,1,30,0.008,1
#%end

#%rules
#%  requires: coastline, coastline_coefficients
#%end

#%option G_OPT_R_INPUT
#% key: coast_geomorphology
#% key_desc: name
#% label: Input map scoring recreation potential in coast
#% description: Coastal geomorphology, scored as suitable to support recreation activities
#% required : no
#% guisection: Water
#%end

#%rules
#%  requires: coast_geomorphology, coastline
#%end

##%option
##% key: geomorphology_coefficients
##% key_desc: Coefficients
##% label: Input distance function coefficients
##% description: Distance function coefficients to compute proximity: distance metric, constant, kappa, alpha and score. Refer to the manual for details.
##% multiple: yes
##% required: no
##% guisection: Water
##% answer: euclidean,1,30,0.008,1
##%end

##%rules
##%  requires: coast_geomorphology, geomorphology_coefficients
##%end

#%option G_OPT_R_INPUT
#% key: bathing_water
#% key_desc: name
#% label: Input bathing water quality map
#% description: Bathing water quality index. The higher, the greater is the recreational value.
#% required : no
#% guisection: Water
#%end

#%option
#% key: bathing_coefficients
#% type: string
#% key_desc: Coefficients
#% label: Input distance function coefficients for the 'bathing_water' map
#% description: Distance function coefficients to compute proximity to bathing waters: distance metric, constant, kappa and alpha. Refer to the manual for details.
#% multiple: yes
#% required: no
#% guisection: Water
#% answer: euclidean,1,5,0.01101
#%end

#%rules
#%  requires: bathing_water, bathing_coefficients
#%end

##%rules
##%  exclusive: lakes
##%  exclusive: coastline
##%  excludes: water, coast_geomorphology, coast_proximity, marine, lakes, lakes_proximity, bathing_water
##%end

'''Natural'''

#%option G_OPT_R_INPUT
#% key: protected
#% key_desc: filename
#% label: Input protected areas map
#% description: Input map depicting natural protected areas
#% required : no
#% guisection: Natural
#%end

#%option G_OPT_R_INPUT
#% key: protected_scores
#% type: string
#% key_desc: rules
#% label: Input recreational value scores for the classes of the 'protected' map
#% description: Scores for recreational value of designated areas. Expected are rules for `r.recode` that correspond to classes of the input land use map. If the 'protected' map is given and 'protected_scores' are not provided, the module will use internal rules for the IUCN categories.
#% required : no
#% guisection: Anthropic
#% answer: 11:11:0,12:12:0.6,2:2:0.8,3:3:0.6,4:4:0.6,5:5:1,6:6:0.8,7:7:0,8:8:0,9:9:0
#%end

##%rules
##% exclusive: natural, protected
##% exclusive: protected, natural
###% requires: protected, protected_scores
##%end

'''Artificial areas'''

#%option G_OPT_R_INPUT
#% key: artificial
#% key_desc: name
#% label: Input map of artificial surfaces
#% description: Partial input map to compute proximity to artificial areas, scored via a distance function
#% required : no
#% guisection: Water
#%end

#%option G_OPT_R_INPUT
#% key: artificial_distances
#% type: string
#% key_desc: rules
#% label: Input distance classification rules
#% description: Categories for distance to artificial surfaces. Expected are rules for `r.recode` that correspond to distance values in the 'artificial' map
#% required : no
#% guisection: Anthropic
#% answer: 0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5
#%end

#%rules
#%  requires: artificial, artificial_distances
#%end

'''Roads'''

#%option G_OPT_R_INPUT
#% key: roads
#% key_desc: name
#% label: Input map of primary road network
#% description: Input map to compute roads proximity, scored based on a distance function
#% required : no
#% guisection: Infrastructure
#%end

#%option G_OPT_R_INPUT
#% key: roads_distances
##% key: roads_scores
#% type: string
#% key_desc: rules
#% label: Input distance classification rules
#% description: Categories for distance to roads. Expected are rules for `r.recode` that correspond to distance values in the roads map
#% required : no
#% guisection: Anthropic
#% answer: 0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5
#%end

#%rules
#%  requires: roads, roads_distances
#%  collective: artificial, roads
#%end

'''Recreation'''

#######################################################################
# Offer input for potential?

# #%option G_OPT_R_OUTPUT
# #% key: recreation_potential
# #% key_desc: name
# #% description: Recreation potential map
# #% required: no
# #% answer: recreation_potential
# #% guisection: Components
# #%end

#
#######################################################################

## Review the following item's "parsing rules"!

##%rules
##%  excludes: infrastructure, roads
##%end

'''Devaluation'''

#%option G_OPT_R_INPUTS
#% key: devaluation
#% key_desc: name
#% label: Input map of devaluing elements
#% description: Maps hindering accessibility to and degrading quality of various resources or infrastructure relating to recreation
#% required : no
#% guisection: Devaluation
#%end

'''MASK'''

#%option G_OPT_R_INPUT
#% key: mask
#% key_desc: name
#% description: A raster map to apply as a MASK
#% required : no
#%end

'''Output'''

#%option G_OPT_R_OUTPUT
#% key: potential
#% key_desc: name
#% label: Output map of recreation potential
#% description: Recreation potential map classified in 3 categories
#% required: no
#% guisection: Output
#%end

#%rules
#%  requires: potential, land, natural, water, landuse, protected, lakes, coastline
#%end

#%option G_OPT_R_OUTPUT
#% key: opportunity
#% key_desc: name
#% label: Output intermediate map of recreation opportunity
#% description: Intermediate step in deriving the 'spectrum' map, classified in 3 categories, meant for expert use
#% required: no
#% guisection: Output
#%end

#%rules
#%  requires: opportunity, infrastructure, roads
#%end

#%option G_OPT_R_OUTPUT
#% key: spectrum
#% key_desc: name
#% label: Output map of recreation spectrum
#% description: Recreation spectrum map classified by default in 9 categories
#% required: no
#% guisection: Output
#%end

#%rules
#%  requires: spectrum, infrastructure, roads
##%  requires: spectrum, landcover
#%  required: land, landcover, landuse
#%end

#%option G_OPT_R_INPUT
#% key: spectrum_distances
#% type: string
#% key_desc: rules
#% label: Input distance classification rules for the 'spectrum' map
#% description: Classes for distance to areas of high recreational spectrum. Expected are rules for `r.recode` that correspond to classes of the input spectrum of recreation use map.
#% required : no
#% guisection: Output
#% answer: 0:1000:1,1000:2000:2,2000:3000:3,3000:4000:4,4000:*:5
#%end

'''Required for Cumulative Opportunity Model'''

#%option G_OPT_R_INPUT
#% key: base
#% key_desc: name
#% description: Input base map for zonal statistics
#% required : no
#%end

#%option G_OPT_V_INPUT
#% key: base_vector
#% key_desc: name
#% description: Input base vector map for zonal statistics
#% required : no
#%end

#%option G_OPT_R_INPUT
#% key: aggregation
#% key_desc: name
#% description: Input map of regions over which to aggregate the actual flow
#% required : no
#%end

#%option G_OPT_R_INPUT
#% key: population
#% key_desc: name
#% description: Input map of population density
#% required : no
#%end

#%option G_OPT_R_OUTPUT
#% key: demand
#% type: string
#% key_desc: name
#% label: Output map of demand distribution
#% description: Demand distribution output map: population density per Local Administrative Unit and areas of high recreational value
#% required : no
#% guisection: Output
#%end

#%option G_OPT_R_OUTPUT
#% key: unmet
#% type: string
#% key_desc: name
#% label: Output map of unmet demand distribution
#% description: Unmet demand distribution output map: population density per Local Administrative Unit and areas of high recreational value
#% required : no
#% guisection: Output
#%end

#%rules
#%  requires_all: demand, population, base
#%  requires: demand, infrastructure, artificial, roads
#%  requires: unmet, demand
#%end

#%option G_OPT_R_OUTPUT
#% key: flow
#% type: string
#% key_desc: name
#% label: Output map of flow
#% description: Flow output map: population (per Local Administrative Unit) near areas of high recreational value
#% required : no
#% guisection: Output
#%end

#%rules
#%  requires_all: flow, population, base
#%  requires: flow, infrastructure, artificial, roads
#%end

#%option G_OPT_F_OUTPUT
#% key: supply
#% key_desc: prefix
#% type: string
#% label: Output prefix for the file name of the supply table CSV
#% description: Supply table CSV output file names will get this prefix
#% multiple: no
#% required: no
#% guisection: Output
#%end

#%option G_OPT_F_OUTPUT
#% key: use
#% key_desc: prefix
#% type: string
#% label: Output prefix for the file name of the supply table CSV
#% description: Supply table CSV output file names will get this prefix
#% multiple: no
#% required: no
#% guisection: Output
#%end

#%rules
#%  requires: opportunity, spectrum, demand, flow, supply
#%  required: potential, spectrum, demand, flow, supply, use
#%end

#%rules
#%  requires: supply, land, natural, water, landuse, protected, lakes, coastline
#%  requires_all: supply, population
#%  requires_all: supply, landcover, land_classes
#%  requires: supply, base, base_vector, aggregation
#%  requires: supply, landcover, landuse
#%  requires_all: use, population
#%  requires: use, base, base_vector, aggregation
#%  requires: use, landcover, landuse
#%end

'''Various'''

#%option
#% key: metric
#% key_desc: Metric
#% label: Distance metric to areas of highest recreation opportunity spectrum
#% description: Distance metric to areas of highest recreation opportunity spectrum
#% multiple: yes
#% options: euclidean,squared,maximum,manhattan,geodesic
#% required: no
#% guisection: Output
#% answer: euclidean
#%end

#%option
#% key: units
#% key_desc: Units
#% label: Units to report
#% description: Units to report the demand distribution
#% multiple: yes
#% options: mi,me,k,a,h,c,p
#% required: no
#% guisection: Output
#% answer: k
#%end

#%option
#% key: timestamp
#% type: string
#% label: Timestamp
#% description: Timestamp for the recreation potential raster map
#% required: no
#%end

# required librairies

import os, sys, subprocess
import datetime, time
import csv
import math
# import heapq

'''Fake a file-like object from an in-script hardcoded string?'''
# import StringIO
# from cStringIO import StringIO

import atexit
import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v

if "GISBASE" not in os.environ:
    g.message(_("You must be in GRASS GIS to run this program."))
    sys.exit(1)

# from scoring_schemes import corine

# globals

global grass_render_directory
grass_render_directory = "/geo/grassdb/render"

global equation, citation, spacy_plus
citation_recreation_potential='Zulian (2014)'
spacy_plus = ' + '
equation = "{result} = {expression}"  # basic equation for mapcalc

global THRESHHOLD_ZERO, THRESHHOLD_0001, THRESHHOLD_0003
THRESHHOLD_ZERO = 0
THRESHHOLD_0001 = 0.0001

global CSV_EXTENSION, COMMA, EUCLIDEAN, NEIGHBORHOOD_SIZE, NEIGHBORHOOD_METHOD
CSV_EXTENSION = '.csv'
COMMA='comma'
EUCLIDEAN='euclidean'
# units='k'
NEIGHBORHOOD_SIZE = 11  # this and below, required for neighborhood_function
NEIGHBORHOOD_METHOD = 'mode'

WATER_PROXIMITY_CONSTANT = 1
WATER_PROXIMITY_KAPPA = 30
WATER_PROXIMITY_ALPHA = 0.008
WATER_PROXIMITY_SCORE = 1
BATHING_WATER_PROXIMITY_CONSTANT = 1
BATHING_WATER_PROXIMITY_KAPPA = 5
BATHING_WATER_PROXIMITY_ALPHA = 0.1101

SUITABILITY_SCORES='''1:1:0:0
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
45:45:0.3:0.3'''

SUITABILITY_SCORES_LABELS='''1 thru 1 = 1 0
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
45 thru 45 = 45 0.3'''

URBAN_ATLAS_CATEGORIES = '''11100
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
'''

URBAN_ATLAS_TO_MAES_NOMENCLATURE='''
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
'''

RECREATION_POTENTIAL_CATEGORIES = '''0.0:0.2:1
0.2:0.4:2
0.4:*:3'''
#artificial_distance_categories=
#'0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5'
RECREATION_OPPORTUNITY_CATEGORIES = RECREATION_POTENTIAL_CATEGORIES

#
## FIXME -- No hardcodings please.
#

POTENTIAL_CATEGORY_LABELS = '''1:Low
2:Moderate
3:High
'''

OPPORTUNITY_CATEGORY_LABELS = '''1:Far
2:Midrange
3:Near
'''

SPECTRUM_CATEGORY_LABELS = '''1:Low provision (far)
2:Low provision (midrange)
3:Low provision (near)
4:Moderate provision (far)
5:Moderate provision (midrange)
6:Moderate provision (near)
7:High provision (far)
8:High provision (midrange)
9:High provision (near)
'''

SPECTRUM_DISTANCE_CATEGORY_LABELS = '''1:0 to 1 km
2:1 to 2 km
3:2 to 3 km
4:3 to 4 km
5:>4 km
'''

#
## FIXME -- No hardcodings please.
#

HIGHEST_RECREATION_CATEGORY = 9

SCORE_COLORS = """ # http://colorbrewer2.org/?type=diverging&scheme=RdYlGn&n=11
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
100.0% 0:104:55"""

POTENTIAL_COLORS = """ # Cubehelix color table generated using:
#   r.colors.cubehelix -dn ncolors=3 map=recreation_potential nrotations=0.33 gamma=1.5 hue=0.9 dark=0.3 output=recreation_potential.colors
0.000% 55:29:66
33.333% 55:29:66
33.333% 157:85:132
66.667% 157:85:132
66.667% 235:184:193
100.000% 235:184:193"""

OPPORTUNITY_COLORS = """# Cubehelix color table generated using:
#   r.colors.cubehelix -dn ncolors=3 map=recreation_potential nrotations=0.33 gamma=1.5 hue=0.9 dark=0.3 output=recreation_potential.colors
0.000% 55:29:66
33.333% 55:29:66
33.333% 157:85:132
66.667% 157:85:132
66.667% 235:184:193
100.000% 235:184:193"""

SPECTRUM_COLORS = """# Cubehelix color table generated using:
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
100.000% 235:184:193"""

MOBILITY_CONSTANT = 1
MOBILITY_COEFFICIENTS = { 0 : (0.02350, 0.00102),
                          1 : (0.02651, 0.00109),
                          2 : (0.05120, 0.00098),
                          3 : (0.10700, 0.00067),
                          4 : (0.06930, 0.00057)}
MOBILITY_SCORE = 52
MOBILITY_COLORS = 'wave'
LANDCOVER_FRACTIONS_COLOR='wave'

METHODS='sum'

# helper functions

def run(cmd, **kwargs):
    """Pass required arguments to grass commands (?)"""
    grass.run_command(cmd, quiet=True, **kwargs)

def tmp_map_name(**kwargs):
    """Return a temporary map name, for example:

    Parameters
    ----------
    name :
        Name of input raster map

    Returns
    -------
    temporary_filename :
        A temporary file name for the input raster map

    Examples
    --------
    >>> tmp_map_name(potential)
    tmp.SomeTemporaryString.potential
    """
    temporary_absolute_filename = grass.tempfile()
    temporary_filename = "tmp." + grass.basename(temporary_absolute_filename)
    if 'name' in kwargs:
        name = kwargs.get('name')
        temporary_filename = temporary_filename + '.' + str(name)
    return temporary_filename

def cleanup():
    """Clean up temporary maps"""

    if rename_at_exit:
        if demand in rename_at_exit:
            g.rename(raster=(demand_copy,demand))

    # get list of temporary maps
    temporary_raster_maps = grass.list_strings(type='raster',
            pattern='tmp.{pid}*'.format(pid=os.getpid()))

    # inform
    if any([temporary_raster_maps, remove_at_exit,
        remove_normal_files_at_exit]):
        g.message("Removing temporary files")

        # remove temporary maps
        if temporary_raster_maps:
            g.remove(flags='f',
                    type="raster",
                    pattern='tmp.{pid}*'.format(pid=os.getpid()),
                    quiet=True)

        # remove raster and vector maps in handcrafted list
        if remove_at_exit:
            g.remove(flags='f',
                    type=('raster','vector'),
                    name=','.join(remove_at_exit),
                    quiet=True)

        # remove normal files at OS level
        if remove_normal_files_at_exit:
            for item in remove_normal_files_at_exit:
                os.unlink(item)

    # # remove MASK ? FIXME
    # if grass.find_file(name='MASK', element='cell')['file']:
    #     r.mask(flags='r', verbose=True)

def string_to_file(string, **kwargs):
    """Split series of strings separated by comma in lines and write as an
    ASCII file

    Parameters
    ----------
    string :
        A string where commas will be replaced by a newline

    kwargs :
        Optional key-word argument 'name'

    Returns
    -------
    filename :
        Name of the ASCII file into where the transformed string is written

    Examples
    --------

    """
    string = string.split(',')
    string = '\n'.join(string)
    # string = string.splitlines()

    msg = "String split in lines: {s}".format(s=string)
    grass.debug(_(msg))

    if 'name' in kwargs:
        name = kwargs.get('name')
    filename = tmp_map_name(name=name)

    # # Use a file-like object instead?
    # import tempfile
    # ascii_file = tempfile.TemporaryFile()

    try:
        ascii_file = open(filename, "w")
        ascii_file.writelines(string)
        # ascii_file.seek(0)  # in case of a file-like object

    # if DEBUG, then do:
        # for line in ascii_file:
        #     grass.debug(_(line.rstrip()))

    except IOError as error:
        print ("IOError :", error)
        return

    finally:
        ascii_file.close()
        return filename  # how would that work with a file-like object?
        # Will be removed right after `.close()` -- How to possibly re-use it
            # outside the function?
        # Wrap complete main() in a `try` statement?

def save_map(mapname):
    """Helper function to save some in-between maps, assisting in debugging

    Parameters
    ----------
    mapname :
        ...

    Returns
    -------
    newname :
        New name for the input raster map

    Examples
    --------
    """
    # run('r.info', map=mapname, flags='r')
    # run('g.copy', raster=(mapname, 'DebuggingMap'))

    #
    # Needs re-design! FIXME
    #

    newname = mapname
    if save_temporary_maps:
        newname = 'output_' + mapname
        run('g.rename', raster=(mapname, newname))
    return newname

def merge_two_dictionaries(a, b):
    """Merge two dictionaries in via shallow copy.
    Source: https://stackoverflow.com/a/26853961/1172302"""
    merged_dictionary = a.copy()
    merged_dictionary.update(b)
    return merged_dictionary

def dictionary_to_csv(filename, dictionary):
    """Write a Python dictionary as CSV named 'filename'

    Parameters
    ----------
    filename :
        Name for output file

    dictionary :
        Name of input Python dictionary to write to 'filename'

    Returns
    -------
        This function does not return anything

    Examples
    --------
    """
    f = open(filename, "wb")
    w = csv.writer(f)

    # write a header
    w.writerow(['category', 'label', 'value'])

    # terminology: from 'base' and 'cover' maps
    for base_key, value in dictionary.items():
        base_category = base_key[0]
        base_label = base_key[1]  # .decode('utf-8')
        if value is None or value == '':
            continue
        w.writerow([base_category,
            base_label,
            value])

    f.close()

def nested_dictionary_to_csv(filename, dictionary):
    """Write out a nested Python dictionary as CSV named 'filename'

    Parameters
    ----------
    filename :
        Name for output file

    dictionary :
        Name of the input Python dictionary
    """
    f = open(filename, "wb")
    w = csv.writer(f)

    # write a header
    w.writerow(['base',
                'base_label',
                'cover',
                'cover_label',
                'area',
                'count',
                'percents'])

    # terminology: from 'base' and 'cover' maps
    for base_key, inner_dictionary in dictionary.items():
        base_category = base_key[0]
        base_label = base_key[1]  # .decode('utf-8')

        for cover_category, inner_value in inner_dictionary.items():
            if inner_value is None or inner_value == '':
                continue
            cover_label = inner_value[0]
            area = inner_value[1]
            pixel_count = inner_value[2]
            pixel_percentage = inner_value[3]
            w.writerow([base_category,
                base_label,
                cover_category,
                cover_label,
                area,
                pixel_count,
                pixel_percentage])

    f.close()

def append_map_to_component(raster, component_name, component_list):
    """Appends raster map to given list of components

    Parameters
    ----------
    raster :
        Input raster map name

    component_name :
        Name of the component to add the raster map to

    component_list :
        List of raster maps to add the input 'raster' map

    Returns
    -------

    Examples
    --------
    ...
    """
    component_list.append(raster)
    msg = "Map {name} included in the '{component}' component"
    msg = msg.format(name=raster, component=component_name)
    grass.verbose(_(msg))

def get_univariate_statistics(raster):
    """
    Return and print basic univariate statistics of the input raster map

    Parameters
    ----------
    raster :
        Name of input raster map

    Returns
    -------
    univariate :
        Univariate statistics min, mean, max and variance of the input raster
        map

    Example
    -------
    ...
    """
    univariate = grass.parse_command('r.univar', flags='g', map=raster)
    if info:
        minimum = univariate['min']
        mean = univariate['mean']
        maximum = univariate['max']
        variance = univariate['variance']
        msg = "min {mn} | mean {avg} | max {mx} | variance {v}"
        msg = msg.format(mn=minimum, avg=mean, mx=maximum, v=variance)
        grass.verbose(_(msg))
    return univariate

def recode_map(raster, rules, colors, output):
    """Scores a raster map based on a set of category recoding rules.

    This is a wrapper around r.recode

    Parameters
    ----------
    raster :
        Name of input raster map

    rules :
        Rules for r.recode

    colors :
        Color rules for r.colors

    output :
        Name of output raster map

    Returns
    -------
        Does not return any value

    Examples
    --------
    ...
    """
    msg = "Setting NULL cells in {name} map to 0"
    msg = msg.format(name=raster)
    grass.debug(_(msg))

    # ------------------------------------------
    r.null(map=raster, null=0)  # Set NULLs to 0
    msg = "To Do: confirm if setting the '{raster}' map's NULL cells to 0 is right"
    msg = msg.format(raster=raster)
    grass.debug(_(msg))
    # Is this right?
    # ------------------------------------------

    r.recode(input=raster,
            rules=rules,
            output=output)

    r.colors(map=output,
            rules='-',
            stdin=SCORE_COLORS,
            quiet=True)

    # if save_temporary_maps:
    #     tmp_output = save_map(output)

    grass.verbose(_("Scored map {name}:".format(name=raster)))

def float_to_integer(double):
    """Converts an FCELL or DCELL raster map into a CELL raster map

    Parameters
    ----------
    double :
            An 'FCELL' or 'DCELL' type raster map

    Returns
    -------
    This function does not return any value

    Examples
    --------
    ..
    """
    expression = 'int({double})'
    expression = expression.format(double=double)
    equation=equation.format(result=double, expression=expression)
    r.mapcalc(equation)

def get_coefficients(coefficients_string):
    """Returns coefficients from an input coefficients_string

    Parameters
    ----------
    coefficients_string:
        One string which lists a metric and coefficients separated by comma
        without spaces

    Returns
    -------
    metric:
        Metric to use an input option to the `r.grow.distance` module

    constant:
        A constant value for the 'attractiveness' function

    kappa:
        A Kappa coefficients for the 'attractiveness' function

    alpha:
        An alpha coefficient for the 'attractiveness' function

    score
        A score value to multiply by the generic 'attractiveness' function

    Examples
    --------
    ...
    """
    coefficients = coefficients_string.split(',')
    msg = "Distance function coefficients: "
    metric = coefficients[0]
    msg += "Metric='{metric}', ".format(metric=metric)
    constant = coefficients[1]
    msg += "Constant='{constant}', ".format(constant=constant)
    kappa = coefficients[2]
    msg += "Kappa='{Kappa}', ".format(Kappa=kappa)
    alpha = coefficients[3]
    msg += "Alpha='{alpha}', ".format(alpha=alpha)
    try:
        if coefficients[4]:
            score = coefficients[4]
            msg += "Score='{score}'".format(score=score)
            grass.verbose(_(msg))
            return metric, constant, kappa, alpha, score
    except IndexError:
        grass.verbose(_("Score not provided"))

    grass.verbose(_(msg))
    return metric, constant, kappa, alpha

def build_distance_function(constant, kappa, alpha, variable, **kwargs):
    """
    Build a valid `r.mapcalc` expression based on the following "space-time"
    function:

        ( {constant} + {kappa} ) / ( {kappa} + exp({alpha} * {variable}) )

    Parameters
    ----------
    constant :
        1

    kappa :
        A constant named 'K'

    alpha :
        A constant named 'a'

    variable :
        The main input variable: for 'attractiveness' it is 'distance', for
        'flow' it is 'population'

    kwargs :
        More keyword arguments such as: 'score', 'suitability'

        score :
            If 'score' is given, it used as a multiplication factor to the base
            equation.

        suitability :
            If 'suitability' is given, it is used as a multiplication factor to
            the base equation.

    Returns
    -------
    function:
        A valid `r.mapcalc` expression

    Examples
    --------
    ..
    """
    numerator = "{constant} + {kappa}"
    numerator = numerator.format(constant = constant, kappa = kappa)

    denominator = "{kappa} + exp({alpha} * {variable})"
    denominator = denominator.format(
            kappa = kappa,
            alpha = alpha,
            variable = variable)  # variable "formatted" by a caller function

    function = " ( {numerator} ) / ( {denominator} )"
    function = function.format(
            numerator = numerator,
            denominator = denominator)
    grass.debug("Function without score: {f}".format(f=function))

    if 'score' in kwargs:
        score = kwargs.get('score')
        function += " * {score}"  # need for float()?
        function = function.format(score=score)
    grass.debug(_("Function after adding 'score': {f}".format(f=function)))

    # Integrate land suitability scores in the distance function ? ------------

    # if 'suitability' in kwargs:
    #     suitability = kwargs.get('suitability')
    #     function += " * {suitability}"  # FIXME : Confirm Correctness
    #     function = function.format(suitability=suitability)
    # msg = "Function after adding 'suitability': {f}".format(f=function)
    # grass.debug(_(msg))

    # -------------------------------------------------------------------------

    del(numerator)
    del(denominator)

    return function

def compute_attractiveness(raster, metric, constant, kappa, alpha, **kwargs):
    """
    Compute a raster map whose values follow an (euclidean) distance function
    ( {constant} + {kappa} ) / ( {kappa} + exp({alpha} * {distance}) ), where:

    Source: http://publications.jrc.ec.europa.eu/repository/bitstream/JRC87585/lb-na-26474-en-n.pd

    Parameters
    ----------
    constant : 1

    kappa :
        A constant named 'K'

    alpha :
        A constant named 'a'

    distance :
        A distance map based on the input raster

    score :
        A score term to multiply the distance function

    kwargs :
        Optional keyword arguments, such as 'mask' and 'output'. The 'mask'
        is inverted to selectively exclude non-NULL cells from distance
        related computations. The 'output' is used to name the computed
        proximity map.

    Returns
    -------
    tmp_output :
        A temporary proximity to features raster map.

    Examples
    --------
    ...

    """
    distance_terms = [str(raster),
                      str(metric),
                      'distance',
                      str(constant),
                      str(kappa),
                      str(alpha)]

    if 'score' in kwargs:
        score = kwargs.get('score')
        grass.debug(_("Score for attractiveness equation: {s}".format(s=score)))
        distance_terms += str(score)

    # tmp_distance = tmp_map_name('_'.join(distance_terms))
    tmp_distance = tmp_map_name(name='_'.join([raster, metric]))
    r.grow_distance(input=raster,
            distance=tmp_distance,
            metric=metric,
            quiet=True,
            overwrite=True)

    if 'mask' in kwargs:
        mask = kwargs.get('mask')
        # global mask
        msg = "Inverted masking to exclude non-NULL cells "
        msg += "from distance related computations based on '{mask}'"
        msg = msg.format(mask=mask)
        grass.verbose(_(msg))
        r.mask(raster=mask, flags='i', overwrite=True, quiet=True)

    # FIXME: use a parameters dictionary, avoid conditionals
    if 'score' in kwargs:
        distance_function = build_distance_function(
                constant=constant,
                kappa=kappa,
                alpha=alpha,
                variable=tmp_distance,
                score=score)

    # FIXME: use a parameters dictionary, avoid conditionals
    if not 'score' in kwargs:
        distance_function = build_distance_function(
                constant=constant,
                kappa=kappa,
                alpha=alpha,
                variable=tmp_distance)

    # temporary maps will be removed
    if 'output_name' in kwargs:
        tmp_distance_map = tmp_map_name(name=kwargs.get('output_name'))
    else:
        basename = '_'.join([raster, 'attractiveness'])
        tmp_distance_map = tmp_map_name(name=basename)

    distance_function = equation.format(result=tmp_distance_map,
            expression=distance_function)

    msg = "Distance function: {f}".format(f=distance_function)
    grass.verbose(_(msg))
    del(msg)

    grass.mapcalc(distance_function, overwrite=True)

    r.null(map=tmp_distance_map, null=0)  # Set NULLs to 0

    compress_status = grass.read_command(
            'r.compress',
            flags='g',
            map=tmp_distance_map)
    grass.verbose(_("Compress status: {s}".format(s=compress_status)))

    del(distance_function)

    tmp_output = save_map(tmp_distance_map)
    return tmp_distance_map

def neighborhood_function(raster, method, size, distance_map):
    """
    Parameters
    ----------
    raster :
        Name of input raster map for which to apply r.neighbors

    method :
        Method for r.neighbors

    size :
        Size for r.neighbors

    distance :
        A distance map

    Returns
    -------
    filtered_output :
        A neighborhood filtered raster map

    Examples
    --------
    ...
    """
    r.null(map=raster, null=0)  # Set NULLs to 0

    neighborhood_output = distance_map + '_' + method
    msg = "Neighborhood operator '{method}' and size '{size}' for map '{name}'"
    msg = msg.format(method=method, size=size, name=neighborhood_output)
    grass.verbose(_(msg))

    r.neighbors(input=raster,
            output=neighborhood_output,
            method=method,
            size=size,
            overwrite=True)

    scoring_function = "{neighborhood} * {distance}"
    scoring_function = scoring_function.format(
            neighborhood=neighborhood_output,
            distance=distance_map)

    filtered_output = distance_map
    filtered_output += '_' + method + '_' + str(size)

    neighborhood_function = equation.format(result=filtered_output,
            expression=scoring_function)
    # ---------------------------------------------------------------
    grass.debug(_("Expression: {e}".format(e=neighborhood_function)))
    # ---------------------------------------------------------------
    grass.mapcalc(neighborhood_function, overwrite=True)

    # tmp_distance_map = filtered_output

    # r.compress(distance_map, flags='g')

    del(method)
    del(size)
    del(neighborhood_output)
    del(scoring_function)
    # del(filtered_output)

    return filtered_output

def smooth_map(raster, method, size):
    """
    Parameters
    ----------
    raster :

    method :

    size :

    Returns
    -------

    Examples
    --------
    """
    r.neighbors(
            input=raster,
            output=raster,
            method=method,
            size=size,
            overwrite=True,
            quiet=True)

def smooth_component(component, method, size):
    """
    component:

    method:

    size:
    """
    try:
        if len(component) > 1:
            for item in component:
                smooth_map(item,
                        method=method,
                        size=size)
        else:
            smooth_map(component[0],
                    method=method,
                    size=size)

    except IndexError:
        grass.verbose(_("Index Error"))  # FIXME: some useful message... ?

def zerofy_small_values(raster, threshhold, output_name):
    """
    Set the input raster map cell values to 0 if they are smaller than the
    given threshhold

    Parameters
    ----------
    raster :
        Name of input raster map

    threshhold :
        Reference for which to flatten smaller raster pixel values to zero

    output_name :
        Name of output raster map

    Returns
    -------
        Does not return any value

    Examples
    --------
    ...
    """
    rounding='if({raster} < {threshhold}, 0, {raster})'
    rounding = rounding.format(raster=raster, threshhold=threshhold)
    rounding_equation = equation.format(result=output_name, expression=rounding)
    grass.mapcalc(rounding_equation, overwrite=True)

def normalize_map (raster, output_name):
    """
    Normalize all raster map cells by subtracting the raster map's minimum and
    dividing by the range.

    Parameters
    ----------
    raster :
        Name of input raster map

    output_name :
        Name of output raster map

    Returns
    -------

    Examples
    --------
    ...
    """
    # grass.debug(_("Input to normalize: {name}".format(name=raster)))
    # grass.debug(_("Ouput: {name}".format(name=output_name)))

    finding = grass.find_file(name=raster, element='cell')

    if not finding['file']:
        grass.fatal("Raster map {name} not found".format(name=raster))
    # else:
    #     grass.debug("Raster map {name} found".format(name=raster))

    # univar_string = grass.read_command('r.univar', flags='g', map=raster)
    # univar_string = univar_string.replace('\n', '| ').replace('\r', '| ')
    # msg = "Univariate statistics: {us}".format(us=univar_string)

    minimum = grass.raster_info(raster)['min']
    grass.debug(_("Minimum: {m}".format(m=minimum)))

    maximum = grass.raster_info(raster)['max']
    grass.debug(_("Maximum: {m}".format(m=maximum)))

    if minimum is None or maximum is None:
        msg = "Minimum and maximum values of the <{raster}> map are 'None'. "
        msg += "The {raster} map may be empty "
        msg += "OR the MASK opacifies all non-NULL cells."
        grass.fatal(_(msg.format(raster=raster)))

    normalisation = 'float(({raster} - {minimum}) / ({maximum} - {minimum}))'
    normalisation = normalisation.format(raster=raster, minimum=minimum,
            maximum=maximum)

    # Maybe this can go in the parent function? 'raster' names are too long!
    if info:
        msg = "Normalization expression: "
        msg += normalisation
        grass.verbose(_(msg))
    #

    normalisation_equation = equation.format(result=output_name,
        expression=normalisation)
    grass.mapcalc(normalisation_equation, overwrite=True)

    get_univariate_statistics(output_name)

    del(minimum)
    del(maximum)
    del(normalisation)
    del(normalisation_equation)

def zerofy_and_normalise_component(components, threshhold, output_name):
    """
    Sums up all maps listed in the given "components" object and derives a
    normalised output.

    To Do:

    * Improve `threshold` handling. What if threshholding is not desired? How
    to skip performing it?

    Parameters
    ----------
    components :
        Input list of raster maps (components)

    threshhold :
        Reference value for which to flatten all smaller raster pixel values to
        zero

    output_name :
        Name of output raster map

    Returns
    -------
    ...

    Examples
    --------
    ...
    """
    msg = "Normalising sum of: "
    msg += ','.join(components)
    grass.debug(_(msg))
    grass.verbose(_(msg))

    if len(components) > 1:

        # prepare string for mapcalc expression
        components = [ name.split('@')[0] for name in components ]
        components_string = spacy_plus.join(components)
        components_string = components_string.replace(' ', '')
        components_string = components_string.replace('+', '_')

        # temporary map names
        tmp_intermediate = tmp_map_name(name=components_string)
        tmp_output = tmp_map_name(name=components_string)

        # build mapcalc expression
        component_expression = spacy_plus.join(components)
        component_equation = equation.format(result=tmp_intermediate,
                expression=component_expression)

        grass.mapcalc(component_equation, overwrite=True)

        del(components_string)
        del(component_expression)
        del(component_equation)

    elif len(components) == 1:
        # temporary map names, if components contains one element
        tmp_intermediate = components[0]
        tmp_output = tmp_map_name(name=tmp_intermediate)

    if threshhold > THRESHHOLD_ZERO:
        msg = "Setting values < {threshhold} in '{raster}' to zero"
        grass.verbose(msg.format(threshhold=threshhold, raster=tmp_intermediate))
        zerofy_small_values(tmp_intermediate, threshhold, tmp_output)

    else:
        tmp_output = tmp_intermediate

    # grass.verbose(_("Temporary map name: {name}".format(name=tmp_output)))
    grass.debug(_("Output map name: {name}".format(name=output_name)))
    # r.info(map=tmp_output, flags='gre')

    ### FIXME

    normalize_map(tmp_output, output_name)

    ### FIXME

    del(tmp_intermediate)
    del(tmp_output)
    del(output_name)

def classify_recreation_component(component, rules, output_name):
    """
    Recode an input recreation component based on given rules

    To Do:

    - Potentially, test range of input recreation component, i.e. ranging in
      [0,1]

    Parameters
    ----------
    component :
        Name of input raster map

    rules :
        Rules for r.recode

    output_name :
        Name for output raster map

    Returns
    -------
        Does not return any value

    Examples
    --------
    ...

    """
    r.recode(input=component,
            rules='-',
            stdin=rules,
            output=output_name)

def compute_artificial_proximity(raster, distance_categories, **kwargs):
    """
    Compute proximity to artificial surfaces

    1. Distance to features
    2. Classify distances

    Parameters
    ----------
    raster :
        Name of input raster map

    distance_categories :
        Category rules to recode the input distance map

    kwargs :
        Optional arguments: output_file

    Returns
    -------
    tmp_output :
        Name of the temporary output map for internal, in-script, re-use

    Examples
    --------
    ...
    """
    artificial_distances = tmp_map_name(name=raster)

    grass.run_command("r.grow.distance",
            input = raster,
            distance = artificial_distances,
            metric = EUCLIDEAN,
            quiet = True,
            overwrite = True)

    if 'output_name' in kwargs:
        # temporary maps will be removed
        tmp_output = tmp_map_name(name=kwargs.get('output_name'))
        grass.debug(_("Pre-defined output map name {name}".format(name=tmp_output)))

    else:
        tmp_output = tmp_map_name(name='artificial_proximity')
        grass.debug(_("Hardcoded temporary map name {name}".format(name=tmp_output)))

    msg = "Computing proximity to '{mapname}'"
    msg = msg.format(mapname=raster)
    grass.verbose(_(msg))
    del(msg)
    grass.run_command("r.recode",
            input = artificial_distances,
            output = tmp_output,
            rules = distance_categories,
            overwrite = True)

    output = grass.find_file(name=tmp_output, element='cell')
    if not output['file']:
        grass.fatal("Proximity map {name} not created!".format(name=raster))
#     else:
#         g.message(_("Output map {name}:".format(name=tmp_output)))

    return tmp_output

def artificial_accessibility_expression(artificial_proximity, roads_proximity):
    """
    Build an r.mapcalc compatible expression to compute accessibility to
    artificial surfaces based on the following accessibility classification
    rules for artificial surfaces:

|-------------------+-------+------------+-------------+--------------+---------|
| Anthropic \ Roads | < 500 | 500 - 1000 | 1000 - 5000 | 5000 - 10000 | > 10000 |
|-------------------+-------+------------+-------------+--------------+---------|
| < 500             | 1     | 1          | 2           | 3            | 4       |
|-------------------+-------+------------+-------------+--------------+---------|
| 500 - 1000        | 1     | 1          | 2           | 3            | 4       |
|-------------------+-------+------------+-------------+--------------+---------|
| 1000 - 5000       | 2     | 2          | 2           | 4            | 5       |
|-------------------+-------+------------+-------------+--------------+---------|
| 5000 - 10000      | 3     | 3          | 4           | 5            | 5       |
|-------------------+-------+------------+-------------+--------------+---------|
| > 10000           | 3     | 4          | 4           | 5            | 5       |
|-------------------+-------+------------+-------------+--------------+---------|

    Parameters
    ----------
    artificial :
        Proximity to artificial surfaces

    roads :
        Proximity to roads

    Returns
    -------
    expression
        Valid r.mapcalc expression


    Examples
    --------
    ...
    """
    expression = ('if( {artificial} <= 2 && {roads} <= 2, 1,'
            ' \ \n if( {artificial} == 1 && {roads} == 3, 2,'
            ' \ \n if( {artificial} == 2 && {roads} == 3, 2,'
            ' \ \n if( {artificial} == 3 && {roads} <= 3, 2,'
            ' \ \n if( {artificial} <= 2 && {roads} == 4, 3,'
            ' \ \n if( {artificial} == 4 && {roads} == 2, 3,'
            ' \ \n if( {artificial} >= 4 && {roads} == 1, 3,'
            ' \ \n if( {artificial} <= 2 && {roads} == 5, 4,'
            ' \ \n if( {artificial} == 3 && {roads} == 4, 4,'
            ' \ \n if( {artificial} >= 4 && {roads} == 3, 4,'
            ' \ \n if( {artificial} == 5 && {roads} == 2, 4,'
            ' \ \n if( {artificial} >= 3 && {roads} == 5, 5,'
            ' \ \n if( {artificial} >= 4 && {roads} == 4, 5)))))))))))))')

    expression = expression.format(artificial=artificial_proximity,
            roads=roads_proximity)
    return expression

def compute_artificial_accessibility(artificial_proximity, roads_proximity, **kwargs):
    """Compute artificial proximity

    Parameters
    ----------
    artificial_proximity :
        Artificial surfaces...

    roads_proximity :
        Road infrastructure

    kwargs :
        Optional input parameters

    Returns
    -------
    output :
        ...

    Examples
    --------
    ...
    """
    artificial = grass.find_file(name=artificial_proximity, element='cell')
    if not artificial['file']:
        grass.fatal("Raster map {name} not found".format(name=artificial_proximity))

    roads = grass.find_file(name=roads_proximity, element='cell')
    if not roads['file']:
        grass.fatal("Raster map {name} not found".format(name=roads_proximity))

    accessibility_expression = artificial_accessibility_expression(
            artificial_proximity,
            roads_proximity)
    if 'output_name' in kwargs:
        # temporary maps will be removed!
        tmp_output = tmp_map_name(name=kwargs.get('output_name'))
    else:
        basename = 'artificial_accessibility'
        tmp_output = tmp_map_name(name=basename)

    accessibility_equation = equation.format(result=tmp_output,
            expression=accessibility_expression)

    if info:
        msg = "Equation for proximity to artificial areas: \n"
        msg += accessibility_equation
        grass.debug(msg)
        del(msg)

    grass.verbose(_("Computing accessibility to artificial surfaces"))
    grass.mapcalc(accessibility_equation, overwrite=True)

    del(accessibility_expression)
    del(accessibility_equation)

    output = save_map(tmp_output)

    return output

def recreation_spectrum_expression(potential, opportunity):
    """
    Build and return a valid mapcalc expression for deriving
    the Recreation Opportunity Spectrum

    |-------------------------+-----+----------+------|
    | Potential / Opportunity | Far | Midrange | Near |
    |-------------------------+-----+----------+------|
    | Low                     | 1   | 2        | 3    |
    |-------------------------+-----+----------+------|
    | Moderate                | 4   | 5        | 6    |
    |-------------------------+-----+----------+------|
    | High                    | 7   | 8        | 9    |
    |-------------------------+-----+----------+------|

    Questions:

    - Why not use `r.cross`?
    - Use DUMMY strings for potential and opportunity raster map names?

    Parameters
    ----------
    potential :
        Map depicting potential for recreation

    opportunity :
        Map depicting opportunity for recreation

    Returns
    -------
    expression :
        A valid r.mapcalc expression

    Examples
    --------
    ...
    """
    expression = ('if( {potential} == 1 && {opportunity} == 1, 1,'
            ' \ \n if( {potential} == 1 && {opportunity} == 2, 2,'
            ' \ \n if( {potential} == 1 && {opportunity} == 3, 3,'
            ' \ \n if( {potential} == 2 && {opportunity} == 1, 4,'
            ' \ \n if( {potential} == 2 && {opportunity} == 2, 5,'
            ' \ \n if( {potential} == 2 && {opportunity} == 3, 6,'
            ' \ \n if( {potential} == 3 && {opportunity} == 1, 7,'
            ' \ \n if( {potential} == 3 && {opportunity} == 2, 8,'
            ' \ \n if( {potential} == 3 && {opportunity} == 3, 9)))))))))')

    expression = expression.format(potential=potential,
            opportunity=opportunity)

    msg = "Recreation Spectrum expression: \n"
    msg += expression
    grass.debug(msg)
    del(msg)

    return expression

def compute_recreation_spectrum(potential, opportunity, spectrum):
    """
    Computes spectrum for recreation based on maps of potential and opportunity
    for recreation

    Parameters
    ----------
    potential :
        Name for input potential for recreation map

    opportunity :
        Name for input opportunity for recreation map

    Returns
    -------
    spectrum :
        Name for output spectrum of recreation map

    Examples
    --------
    ...
    """
    spectrum_expression = recreation_spectrum_expression(
            potential=potential,
            opportunity=opportunity)

    spectrum_equation = equation.format(result=spectrum,
            expression=spectrum_expression)

    if info:
        msg = "Recreation Spectrum equation: \n"
        msg += spectrum_equation
        g.message(msg)
        del(msg)

    grass.mapcalc(spectrum_equation, overwrite=True)

    del(spectrum_expression)
    del(spectrum_equation)
    return spectrum

def update_meta(raster, title):
    """
    Update metadata of given raster map

    Parameters
    ----------
    raster :
        ...

    title :
        ...

    Returns
    -------
        Does not return any value

    Examples
    --------
    ...
    """
    history = '\n' + citation_recreation_potential
    description_string = 'Recreation {raster} map'
    description = description_string.format(raster=raster)

    title = '{title}'.format(title=title)
    units = 'Meters'

    source1 = 'Source 1'
    source2 = 'Source 2'

    r.support(map=raster, title=title, description=description, units=units,
            source1=source1, source2=source2, history=history)

    if timestamp:
        r.timestamp(map=raster, date=timestamp)

    del(history)
    del(description)
    del(title)
    del(units)
    del(source1)
    del(source2)

def export_map(input_name, title, categories, colors, output_name):
    """
    Export a raster map by renaming the (temporary) raster map name
    'input_name' to the requested output raster map name 'output_name'.
    This function is (mainly) used to export either of the intermediate
    recreation 'potential' or 'opportunity' maps.

    Parameters
    ----------
    raster :
        Input raster map name

    title :
        Title for the output raster map

    categories :
        Categories and labels for the output raster map

    colors :
        Colors for the output raster map

    output_name :
        Output raster map name

    Returns
    -------
    output_name :
        This function will return the requested 'output_name'

    Examples
    --------
    ..
    """
    finding = grass.find_file(name=input_name,
            element='cell')
    if not finding['file']:
        grass.fatal("Raster map {name} not found".format(name=input_name))
    del(finding)

    # inform
    msg = "\nOutputting '{raster}' map\n"
    msg = msg.format(raster=input_name)
    grass.verbose(_(msg))
    del(msg)

    # get categories and labels
    raster_categories = 'categories_of_'
    raster_categories += input_name
    raster_category_labels = string_to_file(
            string = categories,
            name = raster_categories)

    # add ascii file to removal list
    remove_normal_files_at_exit.append(raster_category_labels)

    # apply categories and description
    r.category(map=input_name,
            rules=raster_category_labels,
            separator=':')

    # update meta and colors
    update_meta(input_name, title)
    r.colors(map=input_name,
            rules='-',
            stdin=colors,
            quiet=True)
    # rename to requested output name
    g.rename(
            raster=(
                input_name,
                output_name),
            quiet=True)

    return output_name

def mobility_function(distance, constant, coefficients, population, score,
        **kwargs):
    """
    The following 'mobility' function, is identical to the one used in
    `compute_attractiveness()`, excluding, however, the 'score' term:

        if(L10<>0,(1+$D$3)/($D$3+exp(-$E$3*L10))*52,0)

    Source: Excel file provided by the MAES Team, Land Resources, D3

    ------------------------------------------------------------------
    if L<>0; then
      # (1 + D) / (D + exp(-E * L)) * 52)

      #  D: Kappa
      # -E: Alpha -- Note the '-' sign in front of E
      #  L: Population (within boundary, within distance buffer)
    ------------------------------------------------------------------

    Parameters
    ----------

    distance :
        Map of distance categories

    constant :
        Constant for the mobility function

    coefficients :
        A dictionary with a set for coefficients for each distance category, as
        (the example) presented in the following table:

        |----------+---------+---------|
        | Distance | Kappa   | Alpha   |
        |----------+---------+---------|
        | 0 to 1   | 0.02350 | 0.00102 |
        |----------+---------+---------|
        | 1 to 2   | 0.02651 | 0.00109 |
        |----------+---------+---------|
        | 2 to 3   | 0.05120 | 0.00098 |
        |----------+---------+---------|
        | 3 to 4   | 0.10700 | 0.00067 |
        |----------+---------+---------|
        | >4       | 0.06930 | 0.00057 |
        |----------+---------+---------|

        Note, the last distance category is not considered in deriving the
        final "map of visits".

        Note, the Alpha coefficient, is signed with a '-' in the mobility
        function.

    population :
        A map with the distribution of the demand per distance category and
        predefined geometric boundaries (see `r.stats.zonal` deriving the
        'demand' map ).

    score :
        A score value for the mobility function

    **kwargs :
        Optional parameters. For example, the land suitability if integration
        in the build_distance_function() will be successfull.

    Returns
    -------

    mobility_expression :
        A valid mapcalc expression to compute the flow based on the
        predefined function `build_distance_function`.

    Examples
    --------
    ...
    """
    expressions={}  # create a dictionary of expressions

    # Not used. It can be though if integration to build_distance_function() is
    # successfull. ------------------------------------------------------------

    # if 'suitability' in kwargs:
    #     suitability = kwargs.get('suitability')
    # -------------------------------------------------------------------------

    for distance_category, parameters in coefficients.items():

        kappa, alpha = parameters

        # Note, alpha gets a minus, that is: -alpha
        expressions[distance_category]=build_distance_function(
                constant=constant,
                kappa=kappa,
                alpha=-alpha,
                variable=population,
                score=score)
                # suitability=suitability)  # Not used.
                # Maybe it can, though, after successfully testing its
                # integration to build_distance_function().

        grass.debug(_("For distance '{d}':".format(d=distance)))
        grass.debug(_(expressions[distance_category]))

    msg = "Expressions per distance category: {e}".format(e=expressions)
    grass.debug(_(msg))

    # build expressions -- explicit: use the'score' kwarg!
    expression = ('eval( mobility_0 = {expression_0},'
                  ' \ \n mobility_1 = {expression_1},'
                  ' \ \n mobility_2 = {expression_2},'
                  ' \ \n mobility_3 = {expression_3},'
                  ' \ \n distance_0 = {distance} == {distance_category_0},'
                  ' \ \n distance_1 = {distance} == {distance_category_1},'
                  ' \ \n distance_2 = {distance} == {distance_category_2},'
                  ' \ \n distance_3 = {distance} == {distance_category_3},'
                  ' \ \n if( distance_0, mobility_0,'
                  ' \ \n if( distance_1, mobility_1,'
                  ' \ \n if( distance_2, mobility_2,'
                  ' \ \n if( distance_3, mobility_3,'
                  ' \ \n null() )))))')
    grass.debug(_("Mapcalc expression: {e}".format(e=expression)))

    # replace keywords appropriately
        # 'distance' is a map
        # 'distance_category' is a value
        # hence: 'distance' != 'distance_category'
    mobility_expression = expression.format(
            expression_0 = expressions[0],
            expression_1 = expressions[1],
            expression_2 = expressions[2],
            expression_3 = expressions[3],
            distance_category_0 = 0,
            distance_category_1 = 1,
            distance_category_2 = 2,
            distance_category_3 = 3,
            distance = distance)
    # FIXME Make the above more elegant?

    msg = "Big expression (after formatting): {e}".format(e=expression)
    grass.debug(_(msg))

    return mobility_expression

def compute_unmet_demand(distance, constant, coefficients, population, score,
        **kwargs):
    """
    Parameters
    ----------

    distance :
        Map of distance categories

    constant :
        Constant for the mobility function

    coefficients :
        A tuple with coefficients for the last distance category, as
        (the example) presented in the following table:

        |----------+---------+---------|
        | Distance | Kappa   | Alpha   |
        |----------+---------+---------|
        | >4       | 0.06930 | 0.00057 |
        |----------+---------+---------|

        Note, this is the last distance category. See also the
        mobility_function().

        Note, the Alpha coefficient, is signed with a '-' in the mobility
        function.

    population :
        A map with the distribution of the demand per distance category and
        predefined geometric boundaries (see `r.stats.zonal` deriving the
        'unmet demand' map ).

    score :
        A score value for the mobility function

    **kwargs :
        Optional parameters. For example, the land suitability if integration
        in the build_distance_function() will be successfull.

    Returns
    -------

    mobility_expression :
        A valid mapcalc expression to compute the flow based on the
        predefined function `build_distance_function`.

    Examples
    --------
    ...
    """
    distance_category = 4  # Hardcoded! FIXME

    kappa, alpha = coefficients
    unmet_demand_expression = build_distance_function(
            constant=constant,
            kappa=kappa,
            alpha=-alpha,
            variable=population,
            score=score)
            # suitability=suitability)  # Not used. Maybe it can, though,
            # after successfull testing its integration to
            # build_distance_function().

    msg = "Expression for distance category '{d}': {e}"
    msg = msg.format(d=distance_category, e=unmet_demand_expression)
    grass.debug(_(msg))

    # build expressions -- explicit: use the 'score' kwarg!
    expression = ('eval( unmet_demand = {expression},'
                  ' \ \n distance = {distance} == {distance_category},'
                  ' \ \n if( distance, unmet_demand,'
                  ' \ \n null() ))')
    grass.debug(_("Mapcalc expression: {e}".format(e=expression)))

    # replace keywords appropriately
    unmet_demand_expression = expression.format(
            expression = unmet_demand_expression,
            distance = distance,
            distance_category = distance_category)

    msg = "Big expression (after formatting): {e}".format(
            e=unmet_demand_expression)
    grass.debug(_(msg))

    return unmet_demand_expression

def update_vector(vector, raster, methods, column_prefix):
    """

    Parameters
    ----------
    vector :
        Vector map whose attribute table to update with results of the
        v.rast.stats call

    raster :
        Source raster map for statistics

    methods :
        Descriptive statistics for the `v.rast.stats` call

    column_prefix :
        Prefix for the names of the columns created by the `v.rast.stats` call

    Returns
    -------
        This helper function executes `v.rast.stats`. It does not return any
        value.

    Examples
    --------
    ..
    """
    run('v.rast.stats',
            map=vector,
            flags='c',
            raster=raster,
            method=methods,
            column_prefix=column_prefix,
            overwrite=True)
    # grass.verbose(_("Updating vector map '{v}'".format(v=vector)))

def get_raster_statistics(map_one, map_two, separator, flags):
    """
    Parameters
    ----------
    map_one :
        First map as input to `r.stats`

    map_two :
        Second map as input to `r.stats`

    separator :
        Character to use as separator in `r.stats`

    flags :
        Flags for `r.stats`

    Returns
    -------
    dictionary :
        A nested dictionary that holds categorical statistics for both maps
        'map_one' and 'map_two'.

        - The 'outer_key' is the raster category _and_ label of 'map_one'.
        - The 'inner_key' is the raster map category of 'map_two'.
        - The 'inner_value' is the list of statistics for map two, as returned
          for `r.stats`.

        Example of a nested dictionary:

        {(u'3',
            u'Region 3'):
            {u'1': [
                u'355.747658',
                u'6000000.000000',
                u'6',
                u'6.38%'],
            u'3': [
                u'216304.146140',
                u'46000000.000000',
                u'46',
                u'48.94%'],
            u'2': [
                u'26627.415787',
                u'46000000.000000',
                u'46',
                u'48.94%']}}
    """

    statistics = grass.read_command(
            'r.stats',
            input=(map_one, map_two),
            output='-',
            flags=flags,
            separator=separator,
            quiet=True)
    statistics = statistics.split('\n')[:-1]

    dictionary = dict()

    # build a nested dictionary where:
    for row in statistics:
        row = row.split('|')
        outer_key = ( row[0], row[1])
        inner_key = row[2]
        inner_value = row[3:]
        inner_dictionary = {inner_key: inner_value}
        try:
            dictionary[outer_key][inner_key] = inner_value
        except KeyError:
            dictionary[outer_key] = { inner_key : inner_value}

    return dictionary

def compile_use_table(supply):
    """Compile the 'use' table out of a 'supply' table

    Parameters
    ----------
    supply :
        A nested Python dictionary that is compiled when runnning the
        compute_supply() function

    Returns
    -------

    Examples
    --------
    """
    uses = {}
    for outer_key, outer_value in supply.items():
        dictionaries = statistics_dictionary[outer_key]

        use_values = []
        for key, value in dictionaries.items():
            use_value = value[0]
            use_values.append(use_value)

        use_in_key = sum([float(x)
            if not math.isnan(float(x))
            else 0
            for x in use_values])

        try:
            uses[outer_key] = use_in_key
        except KeyError:
            print "Something went wrong in building the use table"

    return uses

def compute_supply(base,
        recreation_spectrum,
        highest_spectrum,
        base_reclassification_rules,
        reclassified_base,
        reclassified_base_title,
        flow,
        flow_map_name,
        aggregation,
        ns_resolution,
        ew_resolution,
        **kwargs):
    """
     Algorithmic description of the "Contribution of Ecosysten Types"

     # FIXME
     '''
     1   B ← {0, .., m-1}     :  Set of aggregational boundaries
     2   T ← {0, .., n-1}     :  Set of land cover types
     3   WE ← 0               :  Set of weighted extents
     4   R ← 0                :  Set of fractions
     5   F ← 0
     6   MASK ← HQR           : High Quality Recreation
     7   foreach {b} ⊆ B do   : for each aggregational boundary 'b'
     8      RB ← 0
     9      foreach {t} ⊆ T do  : for each Land Type
     10         WEt ← Et * Wt   : Weighted Extent = Extent(t) * Weight(t)
     11         WE ← WE⋃{WEt}   : Add to set of Weighted Extents
     12     S ← ∑t∈WEt
     13     foreach t ← T do
     14        Rt ← WEt / ∑WE
     15        R ← R⋃{Rt}
     16     RB ← RB⋃{R}
     '''
     # FIXME

    Parameters
    ----------
    recreation_spectrum:
        Map scoring access to and quality of recreation

    highest_spectrum :
        Expected is a map of areas with highest recreational value (category 9
        as per the report ... )

    base :
        Base land types map for final zonal statistics. Specifically to
        ESTIMAP's recrceation mapping algorithm

    base_reclassification_rules :
        Reclassification rules for the input base map

    reclassified_base :
        Name for the reclassified base cover map

    reclassified_base_title :
        Title for the reclassified base map

    ecosystem_types :

    flow :
        Map of visits, derived from the mobility function, depicting the
        number of people living inside zones 0, 1, 2, 3. Used as a cover map
        for zonal statistics.

    flow_map_name :
        A name for the 'flow' map. This is required when the 'flow' input
        option is not defined by the user, yet some of the requested outputs
        required first the production of the 'flow' map. An example is the
        request for a supply table without requesting the 'flow' map itself.

    aggregation :

    ns_resolution :

    ew_resolution :

    statistics_filename :

    **kwargs :
        Optional keyword arguments, such as: 'csv_prefix'

    ? :
        Land cover class percentages in ROS9 (this is: relative percentage)

    output :
        Supply table (distribution of flow for each land cover class)

    Returns
    -------
    This function produces a map to base the production of a supply table in
    form of CSV.

    Examples
    --------
    """
    # Inputs
    flow_in_base = flow + '_' + base
    base_scores = base + '.scores'

    # Define lists and dictionaries to hold intermediate data
    weighted_extents = {}
    flows = []
    global statistics_dictionary
    statistics_dictionary = {}

    # MASK areas of high quality recreation
    r.mask(raster=highest_spectrum, overwrite=True, quiet=True)

    # Reclassify land cover map to MAES ecosystem types
    r.reclass(input=base,
            rules=base_reclassification_rules,
            output=reclassified_base,
            quiet=True)
    # add to "remove_at_exit" after the reclassified maps!

    # Discard areas out of MASK
    copy_equation = equation.format(result=reclassified_base,
            expression=reclassified_base)
    r.mapcalc(copy_equation, overwrite=True)
    del(copy_equation)

    # Count flow within each land cover category
    r.stats_zonal(base=base,
            flags='r',
            cover=flow_map_name,
            method='sum',
            output=flow_in_base,
            overwrite=True,
            quiet=True)

    # Set colors for "flow" map
    r.colors(map=flow_in_base,
        color=MOBILITY_COLORS,
        quiet=True)

    # Parse aggregation raster categories and labels
    categories = grass.parse_command('r.category',
            map=aggregation,
            delimiter='\t')

    for category in categories:

        # Intermediate names

        cells = highest_spectrum + '.cells' + '.' + category
        remove_at_exit.append(cells)

        extent = highest_spectrum + '.extent' + '.' + category
        remove_at_exit.append(extent)

        weighted = highest_spectrum + '.weighted' + '.' + category
        remove_at_exit.append(weighted)

        fractions = base + '.fractions' + '.' + category
        remove_at_exit.append(fractions)

        flow_category = '_flow_' + category
        flow = base + flow_category
        remove_at_exit.append(flow)

        flow_in_reclassified_base = reclassified_base + '_flow'
        flow_in_category = reclassified_base + flow_category
        del(flow_category)
        flows.append(flow_in_category)  # add to list for patching
        remove_at_exit.append(flow_in_category)

        # Output names

        msg = "Processing aggregation raster category: {r}"
        msg = msg.format(r=category)
        grass.debug(_(msg))
        # g.message(_(msg))
        del(msg)

        # First, set region to extent of the aggregation map
            # and resolution to the one of the population map
        # Note the `-a` flag to g.region: ?
        # To safely modify the region: grass.use_temp_region()  # FIXME
        g.region(raster=aggregation,
                nsres=ns_resolution,
                ewres=ew_resolution,
                flags='a',
                quiet=True)

        msg = "|! Computational resolution matched to {raster}"
        msg = msg.format(raster=aggregation)
        grass.debug(_(msg))
        del(msg)

        # Build MASK for current category & high quality recreation areas
        msg = "Setting category '{c}' of '{a}' as a MASK"
        grass.verbose(_(msg.format(c=category, a=aggregation)))
        del(msg)

        masking = 'if( {spectrum} == {highest_quality_category} && '
        masking += '{aggregation} == {category}, '
        masking += '1, null() )'
        masking = masking.format(
                spectrum=recreation_spectrum,
                highest_quality_category=HIGHEST_RECREATION_CATEGORY,
                aggregation=aggregation,
                category=category)

        masking_equation = equation.format(
                result='MASK',
                expression = masking)

        grass.mapcalc(masking_equation, overwrite=True)

        del(masking)
        del(masking_equation)

        # zoom to MASK
        g.region(zoom='MASK',
                nsres=ns_resolution,
                ewres=ew_resolution,
                quiet=True)

        # Count number of cells within each land category
        r.stats_zonal(
                flags='r',
                base=base,
                cover=highest_spectrum,
                method='count',
                output=cells,
                overwrite=True,
                quiet=True)
        cells_categories = grass.parse_command('r.category',
                map=cells,
                delimiter='\t')
        grass.debug(_("Cells: {c}".format(c=cells_categories)))

        # Build cell category and label rules for `r.category`
        cells_rules = '\n'.join(['{0}:{1}'.format(key, value)
            for key, value
            in cells_categories.items()])
        del(cells_categories)

        # Discard areas out of MASK
        copy_equation = equation.format(result=cells,
                expression=cells)
        r.mapcalc(copy_equation, overwrite=True)
        del(copy_equation)

        # Reassign cell category labels
        r.category(
                map=cells,
                rules='-',
                stdin=cells_rules,
                separator=':')
        del(cells_rules)

        # Compute extent of each land category
        extent_expression = "@{cells} * area()"
        extent_expression = extent_expression.format(cells=cells)
        extent_equation = equation.format(
                result=extent,
                expression=extent_expression)
        r.mapcalc(extent_equation, overwrite=True)

        # Write extent figures as labels
        r.stats_zonal(
                flags='r',
                base=base,
                cover=extent,
                method='average',
                output=extent,
                overwrite=True,
                verbose=False,
                quiet=True)

        # Write land suitability scores as an ASCII file
        suitability_scores_as_labels = string_to_file(
                SUITABILITY_SCORES_LABELS,
                name=reclassified_base)
        remove_normal_files_at_exit.append(suitability_scores_as_labels)

        # Write scores as raster category labels
        r.reclass(input=base,
                output=base_scores,
                rules=suitability_scores_as_labels,
                overwrite=True,
                quiet=True,
                verbose=False)
        remove_at_exit.append(base_scores)

        # Compute weighted extents
        weighted_expression = "@{extent} * float(@{scores})"
        weighted_expression = weighted_expression.format(
                extent=extent,
                scores=base_scores)
        weighted_equation = equation.format(
                result=weighted,
                expression = weighted_expression)
        r.mapcalc(weighted_equation, overwrite=True)

        # Write weighted extent figures as labels
        r.stats_zonal(
                flags='r',
                base=base,
                cover=weighted,
                method='average',
                output=weighted,
                overwrite=True,
                verbose=False,
                quiet=True)

        # Get weighted extents in a dictionary
        weighted_extents = grass.parse_command('r.category',
                map=weighted,
                delimiter='\t')

        # Compute the sum of all weighted extents and add to dictionary
        category_sum = sum([float(x)
            if not math.isnan(float(x))
            else 0
            for x
            in weighted_extents.values()])
        weighted_extents['sum'] = category_sum

        # Create a map to hold fractions of each weighted extent to the sum
        # See also:
        # https://grasswiki.osgeo.org/wiki/LANDSAT#Hint:_Minimal_disk_space_copies
        r.reclass(
                input=base,
                output=fractions,
                rules='-',
                stdin='*=*',
                verbose=False,
                quiet=True)

        # Compute weighted fractions of land types
        fraction_category_label = {key: float(value) / weighted_extents['sum']
                for (key, value)
                in weighted_extents.iteritems()
                if key is not 'sum'}

        # Build fraction category and label rules for `r.category`
        fraction_rules = '\n'.join(['{0}:{1}'.format(key, value)
            for key, value
            in fraction_category_label.items()])
        del(fraction_category_label)

        # Set rules
        r.category(
                map=fractions,
                rules='-',
                stdin=fraction_rules,
                separator=':')
        del(fraction_rules)

        # Assert that sum of fractions is ~1
        fraction_categories = grass.parse_command('r.category',
                map=fractions,
                delimiter='\t')

        fractions_sum = sum([float(x)
            if not math.isnan(float(x))
            else 0
            for x
            in fraction_categories.values()])
        msg = "Fractions: {f}".format(f=fraction_categories)
        grass.debug(_(msg))
        del(msg)

        # g.message(_("Sum: {:.17g}".format(fractions_sum)))
        assert abs(fractions_sum -1 ) < 1.e-6, "Sum of fractions is != 1"

        # Compute flow
        flow_expression = "@{fractions} * @{flow}"
        flow_expression = flow_expression.format(fractions=fractions,
                flow=flow_in_base)
        flow_equation = equation.format(
                result=flow,
                expression=flow_expression)
        r.mapcalc(flow_equation, overwrite=True)

        # Write flow figures as raster category labels
        r.stats_zonal(base=reclassified_base,
                flags='r',
                cover=flow,
                method='sum',
                output=flow_in_category,
                overwrite=True,
                verbose=False,
                quiet=True)

        # Parse flow categories and labels
        flow_categories = grass.parse_command('r.category',
                map=flow_in_category,
                delimiter='\t')
        grass.debug(_("Flow: {c}".format(c=flow_categories)))

        # Build flow category and label rules for `r.category`
        flow_rules = '\n'.join(['{0}:{1}'.format(key, value)
            for key, value
            in flow_categories.items()])
        del(flow_categories)

        # Discard areas out of MASK

        # Check here again!
        # Output patch of all flow maps?

        copy_equation = equation.format(result=flow_in_category,
                expression=flow_in_category)
        r.mapcalc(copy_equation, overwrite=True)
        del(copy_equation)

        # Reassign cell category labels
        r.category(
                map=flow_in_category,
                rules='-',
                stdin=flow_rules,
                separator=':')
        del(flow_rules)

        # Update title
        reclassified_base_title += ' ' + category
        r.support(flow_in_category,
                title=reclassified_base_title)

        # if info:
        #     r.report(flags='hn',
        #             map=(flow_in_category),
        #             units=('k','c','p'))

        if print_only:
            r.stats(input=(flow_in_category),
                    output='-',
                    flags='nacpl',
                    separator=COMMA,
                    quiet=True)

        if not print_only:

            if 'flow_column_name' in kwargs:
                flow_column_name = kwargs.get('flow_column_name')
                flow_column_prefix = flow_column_name + category
            else:
                flow_column_name = 'flow'
                flow_column_prefix = flow_column_name + category

            # Produce vector map(s)
            if 'vector' in kwargs:

                vector = kwargs.get('vector')

                # The following is wrong

                # update_vector(vector=vector,
                #         raster=flow_in_category,
                #         methods=METHODS,
                #         column_prefix=flow_column_prefix)

                # What can be done?

                # Maybe update columns of an existing map from the columns of
                # the following vectorised raster map(s)
                # ?

                r.to_vect(
                        input=flow_in_category,
                        output=flow_in_category,
                        type='area',
                        quiet=True)

                # Value is the ecosystem type
                v.db_renamecolumn(
                        map=flow_in_category,
                        column=('value', 'ecosystem'))

                # New column for flow values
                addcolumn_string = flow_column_name + ' double'
                v.db_addcolumn(
                        map=flow_in_category,
                        columns=addcolumn_string)

                # The raster category 'label' is the 'flow'
                v.db_update(
                        map=flow_in_category,
                        column='flow',
                        query_column='label')
                v.db_dropcolumn(
                        map=flow_in_category,
                        columns='label')

                # Update the aggregation raster categories
                v.db_addcolumn(
                        map=flow_in_category,
                        columns='aggregation_id int')
                v.db_update(
                        map=flow_in_category,
                        column='aggregation_id',
                        value=category)

                v.colors(map=flow_in_category,
                        raster=flow_in_category,
                        quiet=True)

            # get statistics
            dictionary = get_raster_statistics(
                    map_one=aggregation,  # reclassified_base
                    map_two=flow_in_category,
                    separator='|',
                    flags='nlcap')

            # merge 'dictionary' with global 'statistics_dictionary'
            statistics_dictionary = merge_two_dictionaries(
                    statistics_dictionary,
                    dictionary)
            del(dictionary)

        # It is important to remove the MASK!
        r.mask(flags='r', quiet=True)


    # FIXME

    # Add "reclassified_base" map to "remove_at_exit" here, so as to be after
    # all reclassified maps that derive from it

    # remove the map 'reclassified_base'
    # g.remove(flags='f', type='raster', name=reclassified_base, quiet=True)
    # remove_at_exit.append(reclassified_base)

    if not print_only:

        r.patch(flags='',
                input=flows,
                output=flow_in_reclassified_base,
                quiet=True)

        if 'vector' in kwargs:
            # Patch all flow vector maps in one
            v.patch(flags='e',
                    input=flows,
                    output=flow_in_reclassified_base,
                    overwrite=True,
                    quiet=True)

        # export to csv
        if 'supply_filename' in kwargs:

            supply_filename = kwargs.get('supply_filename')
            supply_filename += CSV_EXTENSION
            nested_dictionary_to_csv(supply_filename,
                    statistics_dictionary)
            del(supply_filename)

        if 'use_filename' in kwargs:

            use_filename = kwargs.get('use_filename')
            use_filename += CSV_EXTENSION
            uses = compile_use_table(statistics_dictionary)
            dictionary_to_csv(use_filename, uses)
            del(use_filename)
            del(statistics_dictionary)
            del(uses)

    # Maybe return list of flow maps?  Requires unique flow map names
    return flows

    grass.del_temp_region()  # restoring previous region settings
    # grass.verbose("Original Region restored")

def main():
    """
    Main program
    """

    '''Flags and Options'''

    global average_filter
    average_filter = flags['f']

    global info, save_temporary_maps, print_only
    landuse_extent = flags['e']
    save_temporary_maps = flags['s']
    info = flags['i']
    print_only = flags['p']

    global timestamp
    timestamp = options['timestamp']

    global remove_at_exit, remove_normal_files_at_exit, rename_at_exit
    remove_at_exit = []
    remove_normal_files_at_exit = []
    rename_at_exit = []

    global metric, units
    metric = options['metric']
    units = options['units']
    if len(units) > 1:
        units = units.split(',')

    '''names for input, output, output suffix, options'''

    global mask
    mask = options['mask']

    '''
    following some hard-coded names -- review and remove!
    '''

    land = options['land']
    land_component_map_name = tmp_map_name(name='land_component')

    water = options['water']
    water_component_map_name = tmp_map_name(name='water_component')

    natural = options['natural']
    natural_component_map_name = tmp_map_name(name='natural_component')

    urban = options['urban']
    urban_component_map='urban_component'

    infrastructure = options['infrastructure']
    infrastructure_component_map_name = tmp_map_name(name='infrastructure_component')

    recreation = options['recreation']
    recreation_component_map_name = tmp_map_name(name='recreation_component')

    '''Land components'''

    landuse = options['landuse']
    if landuse:
        # Check datatype: a land use map should be categorical, i.e. of type CELL
        landuse_datatype = grass.raster.raster_info(landuse)['datatype']
        if landuse_datatype != 'CELL':
            msg = ("The '{landuse}' input map "
                    "should be a categorical one "
                    "and of type 'CELL'. "
                    "Perhaps you meant to use the 'land' input option instead?")
            grass.fatal(_(msg.format(landuse=landuse)))

    suitability_map_name = tmp_map_name(name='suitability')
    suitability_scores = options['suitability_scores']

    if landuse and suitability_scores and ':' not in suitability_scores:
        msg = "Suitability scores from file: {scores}."
        msg = msg.format(scores = suitability_scores)
        grass.verbose(_(msg))

    if landuse and not suitability_scores:
        msg = "Using internal rules to score land use classes in '{map}'"
        msg = msg.format(map=landuse)
        grass.warning(_(msg))

        suitability_scores = string_to_file(SUITABILITY_SCORES,
                name=suitability_map_name)
        remove_normal_files_at_exit.append(suitability_scores)

    if landuse and suitability_scores and ':' in suitability_scores:
        msg = "Using provided string of rules to score land use classes in {map}"
        msg = msg.format(map=landuse)
        grass.verbose(_(msg))
        suitability_scores = string_to_file(suitability_scores,
                name=suitability_map_name)
        remove_normal_files_at_exit.append(suitability_scores)


    # FIXME -----------------------------------------------------------------

    # Use one landcover input if supply is requested
    # Use one set of land cover reclassification rules

    landcover = options['landcover']

    if not landcover:
        landcover = landuse
        msg = "Land cover map 'landcover' not given. "
        msg += "Attempt to use the '{landuse}' map to derive areal statistics"
        msg = msg.format(landuse=landuse)
        grass.verbose(_(msg))

    maes_ecosystem_types = 'maes_ecosystem_types'
    maes_ecosystem_types_scores = 'maes_ecosystem_types_scores'
    landcover_reclassification_rules = options['land_classes']

    # if 'land_classes' is a file
    if (landcover and
        landcover_reclassification_rules and
        ':' not in landcover_reclassification_rules):
        msg = "Land cover reclassification rules from file: {rules}."
        msg = msg.format(rules = landcover_reclassification_rules)
        grass.verbose(_(msg))

    # if 'land_classes' not given
    if landcover and not landcover_reclassification_rules:

        # if 'landcover' is not the MAES land cover,
        # then use internal reclassification rules
        # how to test:
            # 1. landcover is not a "MAES" land cover
            # 2. landcover is an Urban Atlas one?

        msg = "Using internal rules to reclassify the '{map}' map"
        msg = msg.format(map=landcover)
        grass.verbose(_(msg))

        landcover_reclassification_rules = string_to_file(
                URBAN_ATLAS_TO_MAES_NOMENCLATURE,
                name=maes_ecosystem_types)
        remove_normal_files_at_exit.append(landcover_reclassification_rules)

        # if landcover is a "MAES" land cover, no need to reclassify!

    if (landuse and
        landcover_reclassification_rules and
        ':' in landcover_reclassification_rules):
        msg = "Using provided string of rules to reclassify the '{map}' map"
        msg = msg.format(map=landcover)
        grass.verbose(_(msg))
        landcover_reclassification_rules =  string_to_file(
                landcover_reclassification_rules,
                name=maes_land_classes)
        remove_normal_files_at_exit.append(landcover_reclassification_rules)

    # FIXME -----------------------------------------------------------------

    '''Water components'''

    lakes = options['lakes']
    lakes_coefficients = options['lakes_coefficients']
    lakes_proximity_map_name = 'lakes_proximity'
    coastline = options['coastline']
    coast_proximity_map_name = 'coast_proximity'
    coast_geomorphology = options['coast_geomorphology']
    # coast_geomorphology_coefficients = options['geomorphology_coefficients']
    coast_geomorphology_map_name = 'coast_geomorphology'
    bathing_water = options['bathing_water']
    bathing_water_coefficients = options['bathing_coefficients']
    bathing_water_proximity_map_name = 'bathing_water_proximity'

    '''Natural components'''

    protected = options['protected']
    protected_scores = options['protected_scores']
    protected_areas_map_name = 'protected_areas'

    '''Artificial areas'''

    artificial = options['artificial']
    artificial_proximity_map_name='artificial_proximity'
    artificial_distance_categories = options['artificial_distances']

    roads = options['roads']
    roads_proximity_map_name = 'roads_proximity'
    roads_distance_categories = options['roads_distances']

    artificial_accessibility_map_name='artificial_accessibility'

    '''Devaluation'''

    devaluation = options['devaluation']

    '''Aggregational boundaries'''

    base = options['base']
    base_vector = options['base_vector']
    aggregation = options['aggregation']

    '''Population'''

    population = options['population']
    if population:
        population_ns_resolution = grass.raster_info(population)['nsres']
        population_ew_resolution = grass.raster_info(population)['ewres']

    '''Outputs'''

    potential_title = "Recreation potential"
    recreation_potential = options['potential']  # intermediate / output
    recreation_potential_map_name = tmp_map_name(name='recreation_potential')

    opportunity_title = "Recreation opportunity"
    recreation_opportunity=options['opportunity']
    recreation_opportunity_map_name='recreation_opportunity'

    spectrum_title = "Recreation spectrum"
    # if options['spectrum']:
    recreation_spectrum = options['spectrum']  # output
    # else:
    #     recreation_spectrum = 'recreation_spectrum'
    # recreation_spectrum_component_map_name =
    #       tmp_map_name(name='recreation_spectrum_component_map')

    spectrum_distance_categories = options['spectrum_distances']
    if ':' in spectrum_distance_categories:
        spectrum_distance_categories = string_to_file(
                spectrum_distance_categories,
                name=recreation_spectrum)
        # remove_at_exit.append(spectrum_distance_categories) -- Not a map!
        remove_normal_files_at_exit.append(spectrum_distance_categories)

    highest_spectrum = 'highest_recreation_spectrum'
    crossmap = 'crossmap'  # REMOVEME

    demand = options['demand']
    unmet_demand = options['unmet']

    flow = options['flow']
    flow_map_name = 'flow'

    supply = options['supply']  # use as CSV filename prefix
    use = options['use']  # use as CSV filename prefix

    """ First, care about the computational region"""

    if mask:
        msg = "Masking NULL cells based on '{mask}'".format(mask=mask)
        grass.verbose(_(msg))
        r.mask(raster=mask, overwrite=True, quiet=True)

    if landuse_extent:
        grass.use_temp_region()  # to safely modify the region
        g.region(flags='p', raster=landuse) # Set region to 'mask'
        msg = "|! Computational resolution matched to {raster}"
        msg = msg.format(raster=landuse)
        g.message(_(msg))

    """Land Component
            or Suitability of Land to Support Recreation Activities (SLSRA)"""

    land_component = []  # a list, use .extend() wherever required

    if land:

        land_component = land.split(',')

    if landuse and suitability_scores:

        msg = "Deriving land suitability from '{landuse}' "
        msg += "based on rules described in file '{rules}'"
        grass.verbose(msg.format(landuse=landuse, rules=suitability_scores))

        # suitability is the 'suitability_map_name'
        recode_map(raster=landuse,
                rules=suitability_scores,
                colors=SCORE_COLORS,
                output=suitability_map_name)

        append_map_to_component(
                raster=suitability_map_name,
                component_name='land',
                component_list=land_component)

    '''Water Component'''

    water_component = []
    water_components = []

    if water:

        water_component = water.split(',')
        msg = "Water component includes currently: {component}"
        msg = msg.format(component=water_component)
        grass.debug(_(msg))
        # grass.verbose(_(msg))

    if lakes:

        if lakes_coefficients:
            metric, constant, kappa, alpha, score = get_coefficients(
                    lakes_coefficients)

        lakes_proximity = compute_attractiveness(
                raster = lakes,
                metric = EUCLIDEAN,
                constant = constant,
                kappa = kappa,
                alpha = alpha,
                score = score,
                mask = lakes)

        del(constant)
        del(kappa)
        del(alpha)
        del(score)

        append_map_to_component(
                raster=lakes_proximity,
                component_name='water',
                component_list=water_components)

    if coastline:

        coast_proximity = compute_attractiveness(
                raster = coastline,
                metric = EUCLIDEAN,
                constant = WATER_PROXIMITY_CONSTANT,
                alpha = WATER_PROXIMITY_ALPHA,
                kappa = WATER_PROXIMITY_KAPPA,
                score = WATER_PROXIMITY_SCORE)

        append_map_to_component(
                raster=coast_proximity,
                component_name='water',
                component_list=water_components)

    if coast_geomorphology:

        try:

            if not coastline:
                msg = "The coastline map is required in order to "
                msg += "compute attractiveness based on the "
                msg += "coast geomorphology raster map"
                msg = msg.format(c=water_component)
                grass.fatal(_(msg))

        except NameError:
            grass.fatal(_("No coast proximity"))

        coast_attractiveness = neighborhood_function(
                raster=coast_geomorphology,
                method = NEIGHBORHOOD_METHOD,
                size = NEIGHBORHOOD_SIZE,
                distance_map=coast_proximity)

        append_map_to_component(
                raster=coast_attractiveness,
                component_name='water',
                component_list=water_components)

    if bathing_water:

        if bathing_water_coefficients:
            metric, constant, kappa, alpha = get_coefficients(
                    bathing_water_coefficients)

        bathing_water_proximity = compute_attractiveness(
                raster = bathing_water,
                metric = EUCLIDEAN,
                constant = constant,
                kappa = kappa,
                alpha = alpha)

        del(constant)
        del(kappa)
        del(alpha)

        append_map_to_component(
                raster=bathing_water_proximity,
                component_name='water',
                component_list=water_components)

    # merge water component related maps in one list
    water_component += water_components

    '''Natural Component'''

    natural_component = []
    natural_components = []

    if natural:

        natural_component = natural.split(',')

    if protected:
        msg = "Scoring protected areas '{protected}' based on '{rules}'"
        grass.verbose(_(msg.format(protected=protected, rules=protected_scores)))

        protected_areas = protected_areas_map_name

        recode_map(raster=protected,
                rules=protected_scores,
                colors=SCORE_COLORS,
                output=protected_areas)

        append_map_to_component(
                raster=protected_areas,
                component_name='natural',
                component_list=natural_components)

    # merge natural resources component related maps in one list
    natural_component += natural_components

    """ Normalize land, water, natural inputs
    and add them to the recreation potential component"""

    recreation_potential_component = []

    if land_component:

        for dummy_index in land_component:

            # remove 'land_map' from 'land_component'
            # process and add it back afterwards
            land_map = land_component.pop(0)

            '''
            This section sets NULL cells to 0.
            Because `r.null` operates on the complete input raster map,
            manually subsetting the input map is required.
            '''
            suitability_map = tmp_map_name(name=land_map)
            subset_land = equation.format(result = suitability_map,
                    expression = land_map)
            r.mapcalc(subset_land)

            grass.debug(_("Setting NULL cells to 0"))  # REMOVEME ?
            r.null(map=suitability_map, null=0)  # Set NULLs to 0

            msg = "\nAdding land suitability map '{suitability}' "
            msg += "to 'Recreation Potential' component\n"
            msg = msg.format(suitability = suitability_map)
            grass.verbose(_(msg))

            # add 'suitability_map' to 'land_component'
            land_component.append(suitability_map)

    if len(land_component) > 1:
        grass.verbose(_("\nNormalize 'Land' component\n"))
        zerofy_and_normalise_component(land_component, THRESHHOLD_ZERO,
                land_component_map_name)
        recreation_potential_component.extend(land_component)
    else:
        recreation_potential_component.extend(land_component)

    if land_component and average_filter:
        smooth_component(
                land_component,
                method='average',
                size=7)

    # remove_at_exit.extend(land_component)

    if len(water_component) > 1:
        grass.verbose(_("\nNormalize 'Water' component\n"))
        zerofy_and_normalise_component(water_component, THRESHHOLD_ZERO,
                water_component_map_name)
        recreation_potential_component.append(water_component_map_name)
    else:
        recreation_potential_component.extend(water_component)

    # remove_at_exit.append(water_component_map_name)

    if len(natural_component) > 1:
        grass.verbose(_("\nNormalize 'Natural' component\n"))
        zerofy_and_normalise_component(
                components=natural_component,
                threshhold=THRESHHOLD_ZERO,
                output_name=natural_component_map_name)
        recreation_potential_component.append(natural_component_map_name)
    else:
        recreation_potential_component.extend(natural_component)

    if natural_component and average_filter:
        smooth_component(
                natural_component,
                method='average',
                size=7)

    # remove_at_exit.append(natural_component_map_name)

    """ Recreation Potential [Output] """

    tmp_recreation_potential = tmp_map_name(name=recreation_potential_map_name)

    msg = "Computing intermediate 'Recreation Potential' map: '{potential}'"
    grass.verbose(_(msg.format(potential=tmp_recreation_potential)))
    grass.debug(_("Maps: {maps}".format(maps=recreation_potential_component)))

    zerofy_and_normalise_component(
            components = recreation_potential_component,
            threshhold = THRESHHOLD_ZERO,
            output_name = tmp_recreation_potential)

    # recode recreation_potential
    tmp_recreation_potential_categories = tmp_map_name(
            name=recreation_potential)

    msg = "\nClassifying '{potential}' map"
    msg = msg.format(potential=tmp_recreation_potential)
    grass.verbose(_(msg))

    classify_recreation_component(
            component = tmp_recreation_potential,
            rules = RECREATION_POTENTIAL_CATEGORIES,
            output_name = tmp_recreation_potential_categories)

    if recreation_potential:

        # export 'recreation_potential' map and
        # use 'output_name' for the temporary 'potential' map for spectrum
        tmp_recreation_potential_categories = export_map(
                input_name = tmp_recreation_potential_categories,
                title = potential_title,
                categories = POTENTIAL_CATEGORY_LABELS,
                colors = POTENTIAL_COLORS,
                output_name = recreation_potential)

    # Infrastructure to access recreational facilities, amenities, services
    # Required for recreation opportunity and successively recreation spectrum

    if infrastructure and not any([recreation_opportunity,
        recreation_spectrum, demand, flow, supply]):
        msg = ("Infrastructure is not required "
        "to derive the 'potential' recreation map.")
        grass.warning(_(msg))

    if any([recreation_opportunity, recreation_spectrum, demand, flow, supply]):

        infrastructure_component = []
        infrastructure_components = []

        if infrastructure:
            infrastructure_component.append(infrastructure)

        '''Artificial surfaces (includung Roads)'''

        if artificial and roads:

            msg = "Roads distance categories: {c}"
            msg = msg.format(c=roads_distance_categories)
            grass.debug(_(msg))
            roads_proximity = compute_artificial_proximity(
                    raster = roads,
                    distance_categories = roads_distance_categories,
                    output_name = roads_proximity_map_name)

            msg = "Artificial distance categories: {c}"
            msg = msg.format(c=artificial_distance_categories)
            grass.debug(_(msg))
            artificial_proximity = compute_artificial_proximity(
                    raster = artificial,
                    distance_categories = artificial_distance_categories,
                    output_name = artificial_proximity_map_name)

            artificial_accessibility = compute_artificial_accessibility(
                    artificial_proximity,
                    roads_proximity,
                    output_name = artificial_accessibility_map_name)

            infrastructure_components.append(artificial_accessibility)

        # merge infrastructure component related maps in one list
        infrastructure_component += infrastructure_components

    # # Recreational facilities, amenities, services

    # recreation_component = []
    # recreation_components = []

    # if recreation:
    #     recreation_component.append(recreation)

    # # merge recreation component related maps in one list
    # recreation_component += recreation_components

    """ Recreation Spectrum """

    if any([recreation_spectrum, demand, flow, supply]):

        recreation_opportunity_component = []

        # input
        zerofy_and_normalise_component(
                components = infrastructure_component,
                threshhold = THRESHHOLD_ZERO,
                output_name = infrastructure_component_map_name)

        recreation_opportunity_component.append(
                infrastructure_component_map_name)

        # # input
        # zerofy_and_normalise_component(recreation_component,
        #         THRESHHOLD_0001, recreation_component_map_name)
        # recreation_opportunity_component.append(recreation_component_map_name)
        # remove_at_exit.append(recreation_component_map_name)

        # intermediate

        # REVIEW --------------------------------------------------------------
        tmp_recreation_opportunity = tmp_map_name(
                name=recreation_opportunity_map_name)
        msg = "Computing intermediate opportunity map '{opportunity}'"
        grass.debug(_(msg.format(opportunity=tmp_recreation_opportunity)))

        grass.verbose(_("\nNormalize 'Recreation Opportunity' component\n"))
        grass.debug(_("Maps: {maps}".format(maps=recreation_opportunity_component)))

        zerofy_and_normalise_component(
                components = recreation_opportunity_component,
                threshhold = THRESHHOLD_0001,
                output_name = tmp_recreation_opportunity)

        # Why threshhold 0.0003? How and why it differs from 0.0001?
        # -------------------------------------------------------------- REVIEW

        msg = "Classifying '{opportunity}' map"
        grass.verbose(msg.format(opportunity=tmp_recreation_opportunity))
        del(msg)

        # recode opportunity_component
        tmp_recreation_opportunity_categories = tmp_map_name(
                name=recreation_opportunity)

        classify_recreation_component(
                component = tmp_recreation_opportunity,
                rules = RECREATION_OPPORTUNITY_CATEGORIES,
                output_name = tmp_recreation_opportunity_categories)

        ''' Recreation Opportunity [Output]'''

        if recreation_opportunity:

            # export 'recreation_opportunity' map and
            # use 'output_name' for the temporary 'potential' map for spectrum
            tmp_recreation_opportunity_categories = export_map(
                    input_name = tmp_recreation_opportunity_categories,
                    title = opportunity_title,
                    categories = OPPORTUNITY_CATEGORY_LABELS,
                    colors = OPPORTUNITY_COLORS,
                    output_name = recreation_opportunity)

        # Recreation Spectrum: Potential + Opportunity [Output]

        if not recreation_spectrum and any([demand, flow, supply]):
            recreation_spectrum = tmp_map_name(name='recreation_spectrum')
            remove_at_exit.append(recreation_spectrum)

        recreation_spectrum = compute_recreation_spectrum(
                potential = tmp_recreation_potential_categories,
                opportunity = tmp_recreation_opportunity_categories,
                spectrum = recreation_spectrum)

        msg = "Writing '{spectrum}' map"
        msg = msg.format(spectrum=recreation_spectrum)
        grass.verbose(_(msg))
        del(msg)
        get_univariate_statistics(recreation_spectrum)

        # get category labels
        spectrum_categories = 'categories_of_'
        spectrum_categories += recreation_spectrum
        spectrum_category_labels = string_to_file(
                SPECTRUM_CATEGORY_LABELS,
                name=spectrum_categories)

        # add to list for removal
        remove_normal_files_at_exit.append(spectrum_category_labels)

        # update category labels, meta and colors
        spectrum_categories = 'categories_of_'

        r.category(map=recreation_spectrum,
                rules=spectrum_category_labels,
                separator=':')

        update_meta(recreation_spectrum, spectrum_title)

        r.colors(map=recreation_spectrum, rules='-', stdin = SPECTRUM_COLORS,
                quiet=True)

        if base_vector:
            update_vector(vector=base_vector,
                    raster=recreation_spectrum,
                    methods=METHODS,
                    column_prefix='spectrum')

    """Valuation Tables"""

    if any([demand, flow, supply, aggregation]):

        '''Highest Recreation Spectrum == 9'''

        expression = "if({spectrum} == {highest_recreation_category}, {spectrum}, null())"
        highest_spectrum_expression = expression.format(
                spectrum=recreation_spectrum,
                highest_recreation_category=HIGHEST_RECREATION_CATEGORY)
        highest_spectrum_equation = equation.format(result=highest_spectrum,
                expression=highest_spectrum_expression)
        r.mapcalc(highest_spectrum_equation, overwrite=True)

        '''Distance map'''

        distance_to_highest_spectrum = tmp_map_name(name=highest_spectrum)
        r.grow_distance(input=highest_spectrum,
                distance=distance_to_highest_spectrum,
                metric=metric,
                quiet=True,
                overwrite=True)

        '''Distance categories'''

        distance_categories_to_highest_spectrum = 'categories_of_'
        distance_categories_to_highest_spectrum += distance_to_highest_spectrum
        remove_at_exit.append(distance_categories_to_highest_spectrum)  # FIXME

        recode_map(raster=distance_to_highest_spectrum,
                rules=spectrum_distance_categories,
                colors=SCORE_COLORS,
                output=distance_categories_to_highest_spectrum)

        spectrum_distance_category_labels = string_to_file(
                SPECTRUM_DISTANCE_CATEGORY_LABELS,
                name=distance_categories_to_highest_spectrum)
        remove_normal_files_at_exit.append(spectrum_distance_category_labels)

        r.category(map=distance_categories_to_highest_spectrum,
                rules=spectrum_distance_category_labels,
                separator=':')

        '''Combine Base map and Distance Categories'''

        tmp_crossmap = tmp_map_name(name=crossmap)
        r.cross(input=(distance_categories_to_highest_spectrum, base),
                flags='z',
                output=tmp_crossmap,
                quiet=True)

        grass.use_temp_region()  # to safely modify the region
        g.region(nsres=population_ns_resolution,
                 ewres=population_ew_resolution,
                 flags='a')  # Resolution should match 'population' FIXME
        msg = "|! Computational extent & resolution matched to {raster}"
        msg = msg.format(raster=landuse)
        grass.verbose(_(msg))

        # if info:
        #     population_statistics = get_univariate_statistics(population)
        #     population_total = population_statistics['sum']
        #     msg = "|i Population statistics: {s}".format(s=population_total)
        #     g.message(_(msg))

        '''Demand Distribution'''

        if any([flow, supply, aggregation]) and not demand:
            demand = tmp_map_name(name='demand')

        r.stats_zonal(base=tmp_crossmap,
                flags='r',
                cover=population,
                method='sum',
                output=demand,
                overwrite=True,
                quiet=True)

        # ------------------------------------------- REMOVEME
        # if info:
        #     r.report(map=demand, units=('k','c','p'))
        # ------------------------------------------- REMOVEME

        # copy 'reclassed' as 'normal' map (r.mapcalc)
            # so as to enable removal of it and its 'base' map
        demand_copy = demand + '_copy'
        copy_expression = "{input_raster}"
        copy_expression = copy_expression.format(input_raster=demand)
        copy_equation = equation.format(result=demand_copy,
                expression=copy_expression)
        r.mapcalc(copy_equation, overwrite=True)

        # remove the reclassed map 'demand'
        g.remove(flags='f', type='raster', name=demand, quiet=True)

        # rename back to 'demand'
        g.rename(raster=(demand_copy,demand), quiet=True)

        if demand and base_vector:
            update_vector(vector=base_vector,
                    raster=demand,
                    methods=METHODS,
                    column_prefix='demand')

        '''Unmet Demand'''

        if unmet_demand:

            # compute unmet demand

            unmet_demand_expression = compute_unmet_demand(
                    distance=distance_categories_to_highest_spectrum,
                    constant=MOBILITY_CONSTANT,
                    coefficients=MOBILITY_COEFFICIENTS[4],
                    population=demand,
                    score=MOBILITY_SCORE)
                    # suitability=suitability)  # Not used.
                    # Maybe it can, though, after successfully testing its
                    # integration to build_distance_function().

            grass.debug(_("Unmet demand function: {f}".format(f=unmet_demand_expression)))

            unmet_demand_equation = equation.format(result=unmet_demand,
                    expression=unmet_demand_expression)
            r.mapcalc(unmet_demand_equation, overwrite=True)

            if base_vector:
                update_vector(vector=base_vector,
                        raster=unmet_demand,
                        methods=METHODS,
                        column_prefix='unmet')

        '''Mobility function'''

        if not flow and any([supply, aggregation]):

            flow = flow_map_name
            remove_at_exit.append(flow)

        if flow or any ([supply, aggregation]):

            mobility_expression = mobility_function(
                    distance=distance_categories_to_highest_spectrum,
                    constant=MOBILITY_CONSTANT,
                    coefficients=MOBILITY_COEFFICIENTS,
                    population=demand,
                    score=MOBILITY_SCORE)
                    # suitability=suitability)  # Not used.
                    # Maybe it can, though, after successfully testing its
                    # integration to build_distance_function().

            msg = "Mobility function: {f}"
            grass.debug(_(msg.format(f=mobility_expression)))
            del(msg)

            '''Flow map'''

            mobility_equation = equation.format(result=flow,
                    expression=mobility_expression)
            r.mapcalc(mobility_equation, overwrite=True)

            if base_vector:
                update_vector(vector=base_vector,
                        raster=flow_map_name,
                        methods=METHODS,
                        column_prefix='flow')

    '''Supply Table'''

    if aggregation:

        supply_parameters = {}

        if supply:
            supply_parameters.update({'supply_filename': supply})

        if use:
            supply_parameters.update({'use_filename': use})

        if base_vector:
            supply_parameters.update({'vector': base_vector})

        compute_supply(
                base = landcover,
                recreation_spectrum = recreation_spectrum,
                highest_spectrum = highest_spectrum,
                base_reclassification_rules = landcover_reclassification_rules,
                reclassified_base = maes_ecosystem_types,
                reclassified_base_title = 'MAES ecosystem types',
                flow = flow,
                flow_map_name = flow_map_name,
                aggregation = aggregation,
                ns_resolution = population_ns_resolution,
                ew_resolution = population_ew_resolution,
                **supply_parameters)

    # restore region
    if landuse_extent:
        grass.del_temp_region()  # restoring previous region settings
        grass.verbose("Original Region restored")

    # print citation
    if info:
        citation = 'Citation: ' + citation_recreation_potential
        g.message(citation)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
