cmake_minimum_required(VERSION 3.22)

project(v.in.ply)

include(build_addon)

set(sources
  body.c
  globals.h
  header.c
  local_proto.h
  main.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    vector
  SOURCES ${sources}
  DOCFILES
    v.in.ply.html
    v.in.ply.md)
