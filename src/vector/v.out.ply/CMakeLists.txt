cmake_minimum_required(VERSION 3.22)

project(v.out.ply)

include(build_addon)

set(sources
  args.c
  body.c
  header.c
  local_proto.h
  main.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    gmath
    vector
  SOURCES ${sources}
  DOCFILES
    v.out.ply.html
    v.out.ply.md)
