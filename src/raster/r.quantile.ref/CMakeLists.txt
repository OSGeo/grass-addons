cmake_minimum_required(VERSION 3.22)

project(r.quantile.ref)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES main.c
  GRASSLIBS
    gis
    raster
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
