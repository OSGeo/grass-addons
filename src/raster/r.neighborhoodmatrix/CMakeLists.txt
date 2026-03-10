cmake_minimum_required(VERSION 3.22)

project(r.neighborhoodmatrix)

include(build_addon)

find_M()

set(sources
  main.c
  pavl.c
  pavl.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
