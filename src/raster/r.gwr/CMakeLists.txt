cmake_minimum_required(VERSION 3.22)

project(r.gwr)

include(build_addon)

find_M()

set(sources
  bufs.c
  bufs.h
  estimate_bw.c
  flag.c
  flag.h
  gwr.c
  gwr.h
  gwra.c
  local_proto.h
  main.c
  pavl.c
  pavl.h
  rclist.c
  rclist.h
  weights.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    gmath
    raster
    segment
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
