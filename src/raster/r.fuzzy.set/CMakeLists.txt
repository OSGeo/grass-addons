cmake_minimum_required(VERSION 3.22)

project(r.fuzzy.set)

include(build_addon)

find_M()

set(sources
  fuzzy.c
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
    boundary.png
    set.png
    shape.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
