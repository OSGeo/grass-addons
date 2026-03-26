cmake_minimum_required(VERSION 3.22)

project(r3.what)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster3d
    vector
  SOURCES main.c
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
