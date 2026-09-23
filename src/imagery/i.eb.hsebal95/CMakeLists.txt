cmake_minimum_required(VERSION 3.22)

project(i.eb.hsebal95)

include(build_addon)

find_M()

set(sources
  dtair_desert.c
  dtair.c
  functions.h
  h_0.c
  h1.c
  main.c
  psi_h.c
  psi_m.c
  rah_0.c
  rah1.c
  roh_air_0.c
  roh_air.c
  sensi_h.c
  U_0.c
  u_star.c
  zom_0.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
