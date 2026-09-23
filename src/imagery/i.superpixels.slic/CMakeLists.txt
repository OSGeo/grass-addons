cmake_minimum_required(VERSION 3.22)

project(i.superpixels.slic)

include(build_addon)

find_M()

set(sources
  cache.c
  cache.h
  main.c
  minsize.c
  pavl.c
  pavl.h
  rclist.c
  rclist.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    imagery
    segment
    raster
  DEPENDS LIBM
  DOCFILES
    i_superpixels_slic.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
