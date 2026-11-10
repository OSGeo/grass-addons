cmake_minimum_required(VERSION 3.22)

project(i.points.auto)

include(build_addon)

set(sources
  cellhd.c
  creat_rand.c
  crs.c
  crs.h
  defs.h
  equ.c
  find_points.c
  globals.h
  group.c
  local_proto.h
  main.c
  overlap.c
  target.c)

find_package(FFTW REQUIRED)
if(FFTW_FOUND)
  add_library(FFTW INTERFACE IMPORTED GLOBAL)
  set_property(TARGET FFTW PROPERTY INTERFACE_LINK_LIBRARIES
                                    ${FFTW_LIBRARIES})
  set_property(TARGET FFTW PROPERTY INTERFACE_INCLUDE_DIRECTORIES
                                    ${FFTW_INCLUDE_DIR})
endif()

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS gis imagery raster gmath
  DEPENDS FFTW
  SOURCES ${sources}
  DOCFILES i.points.auto.html i.points.auto.md)
