cmake_minimum_required(VERSION 3.22)

project(i.spec.unmix)

include(build_addon)

find_M()

set(sources
  global.h
  hist.c
  histogram.c
  main.c
  open.c
  spec_angle.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    gmath
    imagery
    raster
  DEPENDS LIBM
  DOCFILES
    mixed_pixels_spectrum.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
