cmake_minimum_required(VERSION 3.22)

project(r.subdayprecip.design LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_subdayprecip_design_basin.png
    r_subdayprecip_design_h_rast.png
    r_subdayprecip_design_result.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
