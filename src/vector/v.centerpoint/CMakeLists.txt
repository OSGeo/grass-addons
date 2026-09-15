cmake_minimum_required(VERSION 3.22)

project(v.centerpoint)

include(build_addon)

find_M()

set(sources
  areas.c
  lines.c
  local_proto.h
  main.c
  points.c)

set(doc_files
  v.centerpoint.html
  v.centerpoint.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS gis vector
  DEPENDS LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
