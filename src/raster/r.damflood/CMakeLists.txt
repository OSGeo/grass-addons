cmake_minimum_required(VERSION 3.22)

project(r.damflood)

include(build_addon)

find_M()

set(sources
  main.c
  SWE.c
  SWE.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    dam_failure.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
