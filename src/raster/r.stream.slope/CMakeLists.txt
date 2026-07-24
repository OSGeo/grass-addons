cmake_minimum_required(VERSION 3.22)

project(r.stream.slope)

include(build_addon)

find_M()

set(doc_files
    r.stream.slope.html
    r.stream.slope.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  SOURCES main.c
  DOCFILES ${doc_files})
