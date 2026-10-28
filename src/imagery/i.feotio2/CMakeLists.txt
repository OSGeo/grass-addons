cmake_minimum_required(VERSION 3.22)

project(i.feotio2)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    clementine_mapplanet.c
    feo.c
    main.c
    tio2.c
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
