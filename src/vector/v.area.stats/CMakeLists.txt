cmake_minimum_required(VERSION 3.22)

project(v.area.stats)

include(build_addon)

find_M()

set(sources
  areas.c
  export.c
  global.h
  main.c
  parse.c)

set(doc_files
  v.area.stats.html
  v.area.stats.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS gis raster vector
  DEPENDS LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
