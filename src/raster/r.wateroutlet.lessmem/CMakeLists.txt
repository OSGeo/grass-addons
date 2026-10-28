cmake_minimum_required(VERSION 3.22)

project(r.wateroutlet.lessmem)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    global.h
    main.c
    over_cells.c
  GRASSLIBS
    gis
    raster
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
