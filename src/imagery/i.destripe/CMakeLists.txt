cmake_minimum_required(VERSION 3.22)

project(i.destripe)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    fourier.c
    main.c
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
