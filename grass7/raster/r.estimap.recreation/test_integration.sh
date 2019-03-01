#!/bin/bash -
#===============================================================================
#
#          FILE: test_integration_x.sh
#
#         USAGE: ./test_integration_x.sh
#
#   DESCRIPTION:
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: First implementation by pmav99
#        AUTHOR: Nikos Alexandris (), nik@nikosalexandris.net
#  ORGANIZATION:
#       CREATED: 02/08/2019 12:48
#      REVISION:  ---
#===============================================================================

# set -o nounset                              # Treat unset variables as an error
set -xeuo pipefail

# Map and file names of interest
map_names=( demand flow spectrum unmet_demand potential opportunity flow_corine_land_cover_2006 maes_ecosystem_types maes_ecosystem_types_flow )
csv_names=( supply.csv use.csv )

# ------------------- FIXME: check if unnecessarily querying any input maps ---
# # Query existing maps
# for name in "${map_names[@]}" ;do
#   mv -f master."${name}" /tmp
#   r.univar "${name}" > master."${name}"
# done

# csv_names=( supply.csv use.csv )
# for name in "${csv_names[@]}" ;do
#   echo "${name}"
#   mv -f master."${name}" /tmp
#   cp "${name}" master."${name}"
# done
# -----------------------------------------------------------------------------

# First grassy things first
g.region raster=area_of_interest -p

# Clean output maps from previous run(s)
g.remove \
    -f -b \
    type=raster \
    name=demand,flow,maes_ecosystem_types,maes_ecosystem_types_flow,flow_corine_land_cover_2006,opportunity,potential,potential_1,potential_2,potential_3,potential_4,recreation_opportunity,spectrum,highest_recreation_spectrum,demand,unmet,unmet_demand,mobility,crossmap

# Re-run the module
$GRASS_PYTHON r.estimap.recreation/r.estimap.recreation.py \
  --verbose \
  --overwrite \
  mask=area_of_interest \
  land=land_suitability \
  water=water_resources,bathing_water_quality \
  natural=protected_areas \
  infrastructure=distance_to_infrastructure \
  potential=potential \
  opportunity=opportunity \
  spectrum=spectrum \
  demand=demand \
  unmet=unmet_demand \
  flow=flow \
  population=population_2015 \
  base=local_administrative_units \
  landcover=corine_land_cover_2006 \
  aggregation=regions \
  land_classes=corine_accounting_to_maes_land_classes.rules \
  supply=supply \
  use=use

# compare 'master' (old) with 'current' (new) maps
for name in "${map_names[@]}" ;do
    # remove 'old'
    touch current."${name}"
    mv -f current."${name}" /tmp
    # create 'new'
    echo "${name}"
    r.univar "${name}" > current."${name}"
    # compare
    diff master."${name}" current."${name}"
    echo
done

for name in "${csv_names[@]}" ;do
    # remove 'old'
    touch current."${name}"
    mv -f current."${name}" /tmp
    # create 'new' from the module's last run
    echo "${name}"
    mv "${name}" current."${name}"
    # compare
    diff master."${name}" current."${name}"
    echo
done
