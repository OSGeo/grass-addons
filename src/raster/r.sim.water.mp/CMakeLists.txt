cmake_minimum_required(VERSION 3.22)

project(r.sim.water.mp)

include(build_addon)

find_M()
find_OpenMP()

set(sources
  erod.c
  hydro.c
  input.c
  main.c
  observation_points.c
  output.c
  random.c
  simlib.h
  utils.c
  waterglobs.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    bitmap
    gis
    gmath
    linkm
    raster
    vector
  DEPENDS
    LIBM
    OpenMP::OpenMP_C
  DOCFILES
    r_sim_water.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
