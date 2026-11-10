cmake_minimum_required(VERSION 3.22)

project(r.traveltime)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES main.c
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    r_traveltime.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
