cmake_minimum_required(VERSION 3.22)

project(r.stream.snap)

include(build_addon)

find_M()

set(sources
    io.c
    main.c
    points_io.c
    snap.c
)

set(doc_files
    r.stream.snap.html
    r.stream.snap.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
    vector
    segment
    dbmibase
    dbmiclient
    dbmidriver
  DEPENDS
    LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
