cmake_minimum_required(VERSION 3.22)

project(i.water)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    main.c
    water_modis.c
    water.c
  GRASSLIBS
    gis
    raster
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
