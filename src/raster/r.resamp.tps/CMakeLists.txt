cmake_minimum_required(VERSION 3.22)

project(r.regression.series)

include(build_addon)

find_M()

set(sources
  cache.c
  cache.h
  flag.c
  flag.h
  main.c
  pavlrc.c
  pavlrc.h
  rclist.c
  rclist.h
  tps.c
  tps.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
    segment
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
