cmake_minimum_required(VERSION 3.22)

project(i.edge)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    canny.c
    canny.h
    gauss.c
    gauss.h
    main.c
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
