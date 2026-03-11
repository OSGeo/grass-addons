cmake_minimum_required(VERSION 3.22)

project(r.suitability.regions LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_suitability_regions_01.png
    r_suitability_regions_02.png
    r_suitability_regions_03.png
    r_suitability_regions_04.png
    r_suitability_regions_05.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
