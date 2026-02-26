cmake_minimum_required(VERSION 3.22)
project(r.hydrobasin)

include(build_addon)

find_OpenMP()
find_M()

set(sources
    delineate_funcs.h
    delineate.c
    delineate_lessmem.c
    delineate_moremem.c
    gettimeofday.c
    global.h
    main.c
    outlet_list.c
    raster_map.c
    timeval_diff.c)

set(doc_files
    r.hydrobasin.html
    r.hydrobasin.md
    r_hydrobasin_bridge_wsheds.png
    r_hydrobasin_formats.png
    r_hydrobasin_wsheds.png)

build_addon(
  ${PROJECT_NAME}
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
  SOURCES ${sources}
  DOCFILES ${doc_files})
