cmake_minimum_required(VERSION 3.22)

project(r.gdd)

include(build_addon)

find_OpenMP()

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C
  SOURCES main.c
  DOCFILES
    r.gdd.html
    r.gdd.md)
