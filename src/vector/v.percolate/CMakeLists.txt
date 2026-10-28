cmake_minimum_required(VERSION 3.22)

project(v.percolate)

include(build_addon)

find_M()

set(sources
  distance.c
  distance.h
  edge_array.c
  edge_array.h
  file.c
  file.h
  global_vars.h
  groups.c
  groups.h
  main.c
  node.c
  node.h
  percolate.c
  percolate.h
  vector.c
  vector.h)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    vector
  SOURCES ${sources}
  DEPENDS
    LIBM
  DOCFILES
    v.percolate.html
    v.percolate.md)
