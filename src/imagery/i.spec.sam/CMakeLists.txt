cmake_minimum_required(VERSION 3.22)

project(i.spec.sam)

include(build_addon)

find_M()
find_OpenMP()

set(sources
  global.h
  hist.c
  local_proto.h
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
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
