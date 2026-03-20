cmake_minimum_required(VERSION 3.22)

project(r.stream.channel)

include(build_addon)

find_M()

set(sources
  io.c
  io.h
  local_proto.h
  local_vars.h
  main.c
  stream_topology.c
  stream_write.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
    segment
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
