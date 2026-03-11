cmake_minimum_required(VERSION 3.22)

project(r.massmov)

include(build_addon)

find_OpenMP()
find_M()

set(sources
  filters.c
  filters.h
  general_f.c
  general_f.h
  main.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
