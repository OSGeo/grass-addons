cmake_minimum_required(VERSION 3.22)

project(r.convergence)

include(build_addon)

find_M()

set(sources
  local_proto.h
  main.c
  memory.c
  slope_aspect.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    conv.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
