cmake_minimum_required(VERSION 3.22)

project(r.lfp)

include(build_addon)

find_OpenMP()
find_M()

set(sources
  direction.c
  gettimeofday.c
  global.h
  lfp_funcs.h
  main.c
  outlet_list.c
  outlets.c
  point_list.c
  timeval_diff.c
  write.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    raster
    vector
  DEPENDS
    LIBM
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C
  DOCFILES
    r_lfp_custom_formats.png
    r_lfp_elev_state_500m_example.png
    r_lfp_elevation_example.png
    r_lfp_formats.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
