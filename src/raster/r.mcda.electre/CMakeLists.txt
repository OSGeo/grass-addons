cmake_minimum_required(VERSION 3.22)

project(r.mcda.electre)

include(build_addon)

find_M()

set(sources
  dominance.c
  local_proto.h
  main.c)

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
