cmake_minimum_required(VERSION 3.22)

project(r.soils.texture)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    local_include.h
    main.c
  GRASSLIBS
    gis
    raster
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
