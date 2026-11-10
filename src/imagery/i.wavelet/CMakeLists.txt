cmake_minimum_required(VERSION 3.22)

project(i.wavelet)

include(build_addon)

find_M()

set(sources
  arrays.c
  arrays.h
  main.c
  w_daubechies.h
  wt_haar.c
  wt_haar.h
  wt.c
  wt.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    imagery
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
