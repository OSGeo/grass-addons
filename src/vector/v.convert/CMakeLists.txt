cmake_minimum_required(VERSION 3.22)

project(v.convert)

include(build_addon)

find_M()

set(sources
  att.c
  conv.h
  dist.c
  local_proto.h
  main.c
  old2new.c
  read.c
  type.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    dig2
    gis
    raster
    vector
  DEPENDS LIBM
  SOURCES ${sources}
  DOCFILES
    v.convert.html
    v.convert.md)
