#!/usr/bin/env python


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

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

# --- Flags ---

# %Module
# %  description: Implementation of ESTIMAP to support mapping and modelling of ecosystem services (Zulian, 2014)
# %  keywords: estimap
# %  keywords: ecosystem services
# %  keywords: recreation potential
# %End

# %flag
# %  key: r
# %  description: Let the mobility function derive real numbers for the flow
# %end

# %flag
# %  key: e
# %  description: Match computational region to extent of land use map
# %end

# %flag
# %  key: f
# %  description: Filter maps in land and natural components before computing recreation maps
# %end

# %flag
# %  key: s
# %  description: Save temporary maps for debugging
# %end

# %flag
# %  key: i
# %  description: Print out citation and other information
# %end

# %flag
# %  key: p
# %  description: Print out results (i.e. supply table), don't export to file
# %end

"""
exclusive: at most one of the options may be given
required: at least one of the options must be given
requires: if the first option is given, at least one of the subsequent options must also be given
requires_all: if the first option is given, all of the subsequent options must also be given
excludes: if the first option is given, none of the subsequent options may be given
collective: all or nothing; if any option is given, all must be given
"""

# --- Components section ---

# %option G_OPT_R_INPUT
# % key: region
# % type: string
# % key_desc: name
# % label: Input map to set computational extent and region
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: land
# % type: string
# % key_desc: name
# % label: Input map scoring access to and suitability of land resources for recreation
# % description: Arbitrary number of maps scoring access to and land resources suitability of land use classes to support recreation activities
# % required: no
# % guisection: Components
# %end

# %option G_OPT_R_INPUTS
# % key: natural
# % key_desc: name
# % label: Input maps scoring access to and quality of inland natural resources
# % description: Arbitrary number of maps scoring access to and quality of inland natural resources
# % required: no
# % guisection: Components
# %end

# %option G_OPT_R_INPUTS
# % key: water
# % key_desc: name
# % label: Input maps scoring access to and quality of water resources
# % description: Arbitrary number of maps scoring access to and quality of water resources such as lakes, sea, bathing waters and riparian zones
# % required: no
# % guisection: Components
# %end

# %option G_OPT_R_INPUTS
# % key: infrastructure
# % type: string
# % key_desc: name
# % label: Input maps scoring infrastructure to reach locations of recreation activities
# % description: Infrastructure to reach locations of recreation activities [required to derive recreation spectrum map]
# % required: no
# % guisection: Components
# %end

# ---Land---

# %option G_OPT_R_INPUT
# % key: landuse
# % type: string
# % key_desc: name
# % label: Input land features map from which to derive suitability for recreation
# % description: Input to derive suitability of land use classes to support recreation activities. Requires scores, overrides suitability.
# % required: no
# % guisection: Land
# %end

# %rules
# %  exclusive: land
# %end

# %option G_OPT_F_INPUT
# % key: suitability_scores
# % type: string
# % key_desc: filename
# % label: Input recreational suitability scores for the categories of the 'landuse' map
# % description: Scores for suitability of land to support recreation activities. Expected are rules for `r.recode` that correspond to categories of the input 'landuse' map. If the 'landuse' map is given and 'suitability_scores not provided, the module will use internal rules for the CORINE land classes.
# % required: no
# % guisection: Land
# %end

# %rules
# %  excludes: land, suitability_scores
# %end

# %option G_OPT_R_INPUT
# % key: landcover
# % type: string
# % key_desc: name
# % label: Input land cover map from which to derive cover percentages within zones of high recreational value
# % description: Input to derive percentage of land classes within zones of high recreational value.
# % required: no
# % guisection: Land
# %end

# %option G_OPT_F_INPUT
# % key: land_classes
# % type: string
# % key_desc: filename
# % label: Input reclassification rules for the classes of the 'landcover' map
# % description: Expected are rules for `r.reclass` that correspond to classes of the input 'landcover' map. If 'landcover' map is given and 'land_classess' not provided, the module will use internal rules for the Urban Atlas land classes
# % required: no
# % guisection: Land
# %end

# --- Water ---

# %option G_OPT_R_INPUT
# % key: lakes
# % key_desc: name
# % label: Input map of inland waters resources for which to score accessibility
# % description: Map of inland water resources to compute proximity for, score accessibility based on a distance function
# % required: no
# % guisection: Water
# %end

# %option
# % key: lakes_coefficients
# % type: string
# % key_desc: Coefficients
# % label: Input distance function coefficients for the 'lakes' map
# % description: Distance function coefficients to compute proximity: distance metric, constant, kappa, alpha and score. Refer to the manual for details.
# % multiple: yes
# % required: no
# % guisection: Water
# % answer: euclidean,1,30,0.008,1
# %end

##%rules
##%  requires: lakes, lakes_coefficients
##%end

# %option G_OPT_R_INPUT
# % key: coastline
# % key_desc: name
# % label: Input sea coast map for which to compute proximity
# % description: Input map to compute coast proximity, scored based on a distance function
# % required: no
# % guisection: Water
# %end

# %option
# % key: coastline_coefficients
# % key_desc: Coefficients
# % label: Input distance function coefficients for the 'coastline' map
# % description: Distance function coefficients to compute proximity: distance metric, constant, kappa, alpha and score. Refer to the manual for details.
# % multiple: yes
# % required: no
# % guisection: Water
# % answer: euclidean,1,30,0.008,1
# %end

# %rules
# %  requires: coastline, coastline_coefficients
# %end

# %option G_OPT_R_INPUT
# % key: coast_geomorphology
# % key_desc: name
# % label: Input map scoring recreation potential in coast
# % description: Coastal geomorphology, scored as suitable to support recreation activities
# % required: no
# % guisection: Water
# %end

# %rules
# %  requires: coast_geomorphology, coastline
# %end

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

# %option G_OPT_R_INPUT
# % key: bathing_water
# % key_desc: name
# % label: Input bathing water quality map
# % description: Bathing water quality index. The higher, the greater is the recreational value.
# % required: no
# % guisection: Water
# %end

# %option
# % key: bathing_coefficients
# % type: string
# % key_desc: Coefficients
# % label: Input distance function coefficients for the 'bathing_water' map
# % description: Distance function coefficients to compute proximity to bathing waters: distance metric, constant, kappa and alpha. Refer to the manual for details.
# % multiple: yes
# % required: no
# % guisection: Water
# % answer: euclidean,1,5,0.01101
# %end

# %rules
# %  requires: bathing_water, bathing_coefficients
# %end

##%rules
##%  exclusive: lakes
##%  exclusive: coastline
##%  excludes: water, coast_geomorphology, coast_proximity, marine, lakes, lakes_proximity, bathing_water
##%end

# --- Natural ---

# %option G_OPT_R_INPUT
# % key: protected
# % key_desc: filename
# % label: Input protected areas map
# % description: Input map depicting natural protected areas
# % required: no
# % guisection: Natural
# %end

# %option G_OPT_R_INPUT
# % key: protected_scores
# % type: string
# % key_desc: rules
# % label: Input recreational value scores for the classes of the 'protected' map
# % description: Scores for recreational value of designated areas. Expected are rules for `r.recode` that correspond to classes of the input land use map. If the 'protected' map is given and 'protected_scores' are not provided, the module will use internal rules for the IUCN categories.
# % required: no
# % guisection: Anthropic
# % answer: 11:11:0,12:12:0.6,2:2:0.8,3:3:0.6,4:4:0.6,5:5:1,6:6:0.8,7:7:0,8:8:0,9:9:0
# %end

##%rules
##% exclusive: natural, protected
##% exclusive: protected, natural
###% requires: protected, protected_scores
##%end

# --- Artificial areas ---

# %option G_OPT_R_INPUT
# % key: artificial
# % key_desc: name
# % label: Input map of artificial surfaces
# % description: Partial input map to compute proximity to artificial areas, scored via a distance function
# % required: no
# % guisection: Water
# %end

# %option G_OPT_R_INPUT
# % key: artificial_distances
# % type: string
# % key_desc: rules
# % label: Input distance classification rules
# % description: Categories for distance to artificial surfaces. Expected are rules for `r.recode` that correspond to distance values in the 'artificial' map
# % required: no
# % guisection: Anthropic
# % answer: 0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5
# %end

# %rules
# %  requires: artificial, artificial_distances
# %end

# --- Road ---

# %option G_OPT_R_INPUT
# % key: roads
# % key_desc: name
# % label: Input map of primary road network
# % description: Input map to compute roads proximity, scored based on a distance function
# % required: no
# % guisection: Infrastructure
# %end

# %option G_OPT_R_INPUT
# % key: roads_distances
##% key: roads_scores
# % type: string
# % key_desc: rules
# % label: Input distance classification rules
# % description: Categories for distance to roads. Expected are rules for `r.recode` that correspond to distance values in the roads map
# % required: no
# % guisection: Anthropic
# % answer: 0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5
# %end

# %rules
# %  requires: roads, roads_distances
# %  collective: artificial, roads
# %end

# --- Recreation ---

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

# --- MASK ---

# %option G_OPT_R_INPUT
# % key: mask
# % key_desc: name
# % description: A raster map to apply as a MASK
# % required: no
# %end

# --- Output ---

# %option G_OPT_R_OUTPUT
# % key: potential
# % key_desc: name
# % label: Output map of recreation potential
# % description: Recreation potential map classified in 3 categories
# % required: no
# % guisection: Output
# %end

# %rules
# %  requires: potential, land, natural, water, landuse, protected, lakes, coastline
# %  requires_all: -e, landuse
# %end

# %option G_OPT_R_OUTPUT
# % key: opportunity
# % key_desc: name
# % label: Output intermediate map of recreation opportunity
# % description: Intermediate step in deriving the 'spectrum' map, classified in 3 categories, meant for expert use
# % required: no
# % guisection: Output
# %end

# %rules
# %  requires: opportunity, infrastructure, roads
# %end

# %option G_OPT_R_OUTPUT
# % key: spectrum
# % key_desc: name
# % label: Output map of recreation spectrum
# % description: Recreation spectrum map classified by default in 9 categories
# % required: no
# % guisection: Output
# %end

# %rules
# %  requires: spectrum, infrastructure, roads
##%  requires: spectrum, landcover
# %  required: land, landcover, landuse
# %end

# %option G_OPT_R_INPUT
# % key: spectrum_distances
# % type: string
# % key_desc: rules
# % label: Input distance classification rules for the 'spectrum' map
# % description: Classes for distance to areas of high recreational spectrum. Expected are rules for `r.recode` that correspond to classes of the input spectrum of recreation use map.
# % required: no
# % guisection: Output
# % answer: 0:1000:1,1000:2000:2,2000:3000:3,3000:4000:4,4000:*:5
# %end

# --- Required for Cumulative Opportunity Model ---

# %option G_OPT_R_INPUT
# % key: base
# % key_desc: name
# % description: Input base map for zonal statistics
# % required: no
# %end

# %option G_OPT_V_INPUT
# % key: base_vector
# % key_desc: name
# % description: Input base vector map for zonal statistics
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: aggregation
# % key_desc: name
# % description: Input map of regions over which to aggregate the actual flow
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: population
# % key_desc: name
# % description: Input map of population density
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: demand
# % type: string
# % key_desc: name
# % label: Output map of demand distribution
# % description: Demand distribution output map: population density per Local Administrative Unit and areas of high recreational value
# % required: no
# % guisection: Output
# %end

# %option G_OPT_R_OUTPUT
# % key: unmet
# % type: string
# % key_desc: name
# % label: Output map of unmet demand distribution
# % description: Unmet demand distribution output map: population density per Local Administrative Unit and areas of high recreational value
# % required: no
# % guisection: Output
# %end

# %rules
# %  requires_all: demand, population, base
# %  requires: demand, infrastructure, artificial, roads
# %  requires: unmet, demand
# %end

# %option G_OPT_R_OUTPUT
# % key: flow
# % type: string
# % key_desc: name
# % label: Output map of flow
# % description: Flow output map: population (per Local Administrative Unit) near areas of high recreational value
# % required: no
# % guisection: Output
# %end

# %rules
# %  requires_all: flow, population, base
# %  requires: flow, infrastructure, artificial, roads
# %end

# %option G_OPT_F_OUTPUT
# % key: supply
# % key_desc: filename
# % type: string
# % label: Output absolute file name for the supply table
# % description: Supply table CSV output file name
# % multiple: no
# % required: no
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key: use
# % key_desc: filename
# % type: string
# % label: Output absolute file name for the use table
# % description: Use table CSV output file name
# % multiple: no
# % required: no
# % guisection: Output
# %end

# %rules
# %  requires: opportunity, spectrum, demand, flow, supply
# %  required: potential, spectrum, demand, flow, supply, use
# %end

# %rules
# %  requires: supply, land, natural, water, landuse, protected, lakes, coastline
# %  requires_all: supply, population, aggregation
# %  requires_all: supply, landcover, land_classes
# %  requires: supply, base, base_vector
# %  requires: supply, landcover, landuse
# %  requires_all: use, population, aggregation
# %  requires: use, base, base_vector, aggregation
# %  requires: use, landcover, landuse
# %end

# --- Various ---

# %option
# % key: metric
# % key_desc: Metric
# % label: Distance metric to areas of highest recreation opportunity spectrum
# % description: Distance metric to areas of highest recreation opportunity spectrum
# % multiple: yes
# % options: euclidean,squared,maximum,manhattan,geodesic
# % required: no
# % guisection: Output
# % answer: euclidean
# %end

# %option
# % key: units
# % key_desc: Units
# % label: Units to report
# % description: Units to report the demand distribution
# % multiple: yes
# % options: mi,me,k,a,h,c,p
# % required: no
# % guisection: Output
# % answer: k
# %end

# %option
# % key: timestamp
# % type: string
# % label: Timestamp
# % description: Timestamp for the recreation potential raster map
# % required: no
# %end

# required librairies

import os
import sys

if "GISBASE" not in os.environ:
    sys.exit("Exiting: You must be in GRASS GIS to run this program.")

import grass.script as grass
from grass.script.utils import set_path

addon_path = os.path.join(
    os.path.dirname(__file__), "..", "etc", "r.estimap.recreation"
)
sys.path.insert(1, os.path.abspath(addon_path))
# import pprint
# pprint.pprint(sys.path)
from estimap_recreation.main import main as main_estimap


def main(options, flags):
    sys.exit(main_estimap(options, flags))


if __name__ == "__main__":
    options, flags = grass.parser()
    main(options, flags)
