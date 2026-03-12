cmake_minimum_required(VERSION 3.22)

project(i.rotate)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    main.c
  GRASSLIBS
    gis
    gproj
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
