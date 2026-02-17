cmake_minimum_required(VERSION 3.22)

project(v.greedycolors)

include(build_addon)

find_M()

set(sources
  main.c
  prb.c
  prb.h)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    vector
  DEPENDS
    LIBM
  SOURCES ${sources}
  DOCFILES
    v.greedycolors.html
    v.greedycolors.md)
