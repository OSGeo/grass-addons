cmake_minimum_required(VERSION 3.22)

project(r.area.createweight LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_area_createweight_census_final.png
    r_area_createweight_census_initial.png
    r_area_createweight_census_merge.png
    r_area_createweight_distance_streets.png
    r_area_createweight_gridded_spatial_units.png
    r_area_createweight_importances_plot_names.png
    r_area_createweight_importances_plot_nonames.png
    r_area_createweight_input_spatial_units.png
    r_area_createweight_overlap_admin.png
    r_area_createweight_weights.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
