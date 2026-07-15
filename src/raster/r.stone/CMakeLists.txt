cmake_minimum_required(VERSION 3.22)

project(r.stone)

include(build_addon)

find_M()

set(sources
  fixed_parameters.c
  fixed_parameters.h
  future_parameters.c
  future_parameters.h
  main.c
  mmath.c
  mmath.h
  points.c
  random2.c
  random2.h
  stone.c
  stone.h
  utils.c
  utils.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    counters.png
    dem_source.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
