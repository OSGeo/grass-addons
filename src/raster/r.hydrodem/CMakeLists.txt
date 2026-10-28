cmake_minimum_required(VERSION 3.22)

project(r.hydrodem)

include(build_addon)

find_M()

set(sources
  bseg.c
  close.c
  cseg.c
  do_astar.c
  dseg.c
  flag.h
  hydro_con.c
  init_search.c
  load.c
  local_proto.h
  main.c
  seg.c
  seg.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
    segment
    vector
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
