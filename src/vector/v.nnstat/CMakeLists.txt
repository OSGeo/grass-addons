cmake_minimum_required(VERSION 3.22)

project(v.nnstat)

include(build_addon)

find_M()

set(sources
  getval.c
  hull.h
  local_proto.h
  macros.h
  main.c
  mbb.c
  mbb.h
  mbr.c
  nearest_neighbour.c
  spatial_index.c
  utils.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    gmath
    rtree
    vector
  SOURCES ${sources}
  DEPENDS
    LIBM
  DOCFILES
   v.nnstat.html
   v.nnstat.md)
