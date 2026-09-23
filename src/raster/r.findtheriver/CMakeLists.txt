cmake_minimum_required(VERSION 3.22)

project(r.findtheriver)

include(build_addon)

find_M()

set(sources
  find_stream.c
  global.h
  main.c
  point_list.c)

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
