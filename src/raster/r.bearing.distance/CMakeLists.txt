cmake_minimum_required(VERSION 3.22)

project(r.bearing.distance)

include(build_addon)

find_M()

set(sources
  azimuth.c
  azimuth.h
  file.c
  file.h
  global_vars.h
  main.c
  raster_file.c
  raster_file.h)

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
