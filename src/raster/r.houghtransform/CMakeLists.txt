cmake_minimum_required(VERSION 3.22)

project(r.houghtransform)

include(build_addon)

find_M()

set(sources
  hough.cpp
  hough.h
  houghparameters.h
  houghtransform.cpp
  houghtransform.h
  linesegmentsextractor.cpp
  linesegmentsextractor.h
  main.cpp
  matrix.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    gmath
    raster
    vector
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
