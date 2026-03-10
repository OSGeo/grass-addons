cmake_minimum_required(VERSION 3.22)

project(r.univar2)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    globals.h
    r.univar_main.c
    sort.c
    stats.c
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
