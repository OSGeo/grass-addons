cmake_minimum_required(VERSION 3.22)

project(i.hyper.atcorr)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES main.c
  GRASSLIBS
    gis
    raster
    raster3d
  DEPENDS
    grass_sixsv
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
