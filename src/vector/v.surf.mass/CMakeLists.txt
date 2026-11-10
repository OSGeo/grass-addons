cmake_minimum_required(VERSION 3.22)

project(v.surf.mass)

include(build_addon)

find_M()

set(sources
  globals.h
  main.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    vector
    raster
    segment
  SOURCES ${sources}
  DEPENDS
    LIBM
  DOCFILES
    v_surf_mass_pycno.png
    v_surf_mass_voronoi.png
    v.surf.mass.html
    v.surf.mass.md)
