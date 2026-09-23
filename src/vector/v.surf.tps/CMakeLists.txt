cmake_minimum_required(VERSION 3.22)

project(v.surf.tps)

include(build_addon)

find_M()

set(sources
  flag.c
  flag.h
  main.c
  rclist.c
  rclist.h
  tps.c
  tps.h)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    btree2
    dbmibase
    dbmiclient
    gis
    vector
    raster
    segment
  SOURCES ${sources}
  DEPENDS
    LIBM
  DOCFILES
    v_surf_tps.png
    v.surf.tps.html
    v.surf.tps.md)
