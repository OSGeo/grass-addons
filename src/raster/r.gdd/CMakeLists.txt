cmake_minimum_required(VERSION 3.22)

project(r.gdd)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
  SOURCES main.c
  DOCFILES
    r.gdd.html
    r.gdd.md)
