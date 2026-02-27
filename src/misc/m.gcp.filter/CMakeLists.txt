cmake_minimum_required(VERSION 3.22)

project(m.gcp.filter)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES main.c
  GRASSLIBS
    gis
    imagery
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
