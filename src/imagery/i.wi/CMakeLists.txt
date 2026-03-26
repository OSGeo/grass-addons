cmake_minimum_required(VERSION 3.22)

project(i.wi)

include(build_addon)

find_M()

set(sources
  awei.c
  lswi.c
  main.c
  ndwi.c
  tcw.c
  wi.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
