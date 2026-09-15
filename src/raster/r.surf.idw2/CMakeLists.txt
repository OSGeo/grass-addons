cmake_minimum_required(VERSION 3.22)

project(r.surf.idw2)

include(build_addon)

set(sources
  local_proto.h
  main.c
  read_cell.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
  SOURCES ${sources}
  DOCFILES
  ${PROJECT_NAME}.html
  ${PROJECT_NAME}.md)
