cmake_minimum_required(VERSION 3.22)

project(v.vol.idw)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    vector
    raster3d
  SOURCES "main.c"
  DEPENDS
    LIBM
  DOCFILES
    v.vol.idw.html
    v.vol.idw.md)
