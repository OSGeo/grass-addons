cmake_minimum_required(VERSION 3.22)

project(r.stream.basins)

include(build_addon)

find_M()

set(sources
    basins_fill.c
    basins_inputs.c
    io.c
    main.c)

set(doc_files
    r.stream.basins.html
    r.stream.basins.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
    dbmibase
    dbmiclient
    dbmidriver
    segment
    vector
  DEPENDS
    LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
