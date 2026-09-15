cmake_minimum_required(VERSION 3.22)

project(r.fuzzy.system)

include(build_addon)

find_M()

set(sources
  fuzzylogic.c
  helpers.c
  io.c
  local_proto.h
  main.c
  map_parser.c
  rule_parser.c
  system.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    f_result.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
