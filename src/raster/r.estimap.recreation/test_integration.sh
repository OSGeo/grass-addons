#!/bin/bash -
#===============================================================================
#
#          FILE: test_integration.sh
#
#         USAGE: ./test_integration.sh
#
#   DESCRIPTION:
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: With contributions by Panos Mavrogiorgos (pmav99)
#        AUTHOR: Nikos Alexandris (), nik@nikosalexandris.net
#  ORGANIZATION:
#       CREATED: 2019/02/08 12:48
# LAST REVISION: 2019/06/06
#===============================================================================

set -o nounset                              # Treat unset variables as an error
# set -xeuo pipefail

# Map and file names of interest
map_names=( output_demand output_flow output_spectrum output_unmet_demand output_potential output_opportunity )
csv_names=( output_supply.csv output_use.csv )

# # ------------------- FIXME: check if unnecessarily querying any input maps ---
# # Query existing maps
# for name in "${map_names[@]}" ;do
#   mv -f master."${name}" /tmp
#   r.univar "${name}" > master."${name}"
# done

# csv_names=( output_supply.csv output_use.csv )
# for name in "${csv_names[@]}" ;do
#   echo "${name}"
#   mv -f master."${name}" /tmp
#   cp "${name}" master."${name}"
# done
# # -----------------------------------------------------------------------------

# First grassy things first
g.region raster=input_area_of_interest -p

# Clean output maps from previous run(s)
g.remove \
    -f -b \
    type=raster \
    name=flow,flow_corine_land_cover_2006,regions,spectrum,unmet_demand,urban_green,water_resources,opportunity,out_potential,population_2015,potential,protected_areas,distance_to_infrastructure,demand,corine_land_cover_2006_row,corine_land_cover_2006,bathing_water_quality,area_of_interest,area_of_corine_land_cover_2006,WHATEVER_corine_land_cover_2006,WHATEVER,land_suitability,land_use,local_administrative_units,local_administrative_units_AT,maes_ecosystem_types,maes_ecosystem_types_flow,highest_recreation_spectrum,corine_land_cover_2006 -fb
g.remove \
    -f -b \
    type=raster \
    pattern=output_*

# Re-run the module
r.estimap.recreation \
  --verbose \
  --overwrite \
  mask=input_area_of_interest \
  land=input_land_suitability \
  water=input_water_resources,input_bathing_water_quality \
  natural=input_protected_areas \
  infrastructure=input_distance_to_infrastructure \
  population=input_population_2015 \
  base=input_local_administrative_units \
  landcover=input_corine_land_cover_2006 \
  aggregation=input_regions \
  land_classes=corine_accounting_to_maes_land_classes.rules \
  population=input_population_2015 \
  base=input_local_administrative_units \
  landcover=input_corine_land_cover_2006 \
  aggregation=input_regions \
  land_classes=corine_accounting_to_maes_land_classes.rules \
  potential=output_potential \
  opportunity=output_opportunity \
  spectrum=output_spectrum \
  demand=output_demand \
  unmet=output_unmet_demand \
  flow=output_flow \
  supply=output_supply \
  use=output_use

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
