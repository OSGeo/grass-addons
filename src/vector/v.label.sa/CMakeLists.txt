cmake_minimum_required(VERSION 3.22)

project(v.label.sa)

include(build_addon)

find_M()
find_package(Freetype REQUIRED)

set(sources
  annealing.c
  font.c
  labels.c
  labels.h
  main.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dig2
    display
    dbmibase
    dbmiclient
    gis
    raster
    vector
  SOURCES ${sources}
  DEPENDS
    Freetype::Freetype
    LIBM
  DOCFILES
    v_label_sa.jpg
    v.label.sa.html
    v.label.sa.md)
