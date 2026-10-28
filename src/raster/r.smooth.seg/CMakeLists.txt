cmake_minimum_required(VERSION 3.22)

project(r.smooth.seg)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    main.c
    varseg.c
    varseg.h
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
