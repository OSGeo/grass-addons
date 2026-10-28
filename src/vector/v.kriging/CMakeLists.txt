cmake_minimum_required(VERSION 3.22)

project(v.kriging)

include(build_addon)

find_M()

set(sources
  geostat.c
  getval.c
  local_proto.h
  main.c
  quantile.c
  spatial_index.c
  stat.c
  utils_kriging.c
  utils_raster.c
  utils_write.c
  utils.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    gmath
    raster
    raster3d
    rtree
    vector
  SOURCES ${sources}
  DEPENDS
    LIBM
  DOCFILES
    v.kriging.html
    v.kriging.md)
