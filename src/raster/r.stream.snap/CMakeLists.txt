cmake_minimum_required(VERSION 3.22)

project(r.stream.snap)

include(build_addon)

find_M()

set(sources
    io.c
    io.h
    local_proto.h
    local_vars.h
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
    dbmibase
    dbmiclient
    gis
    raster
    segment
    vector
  DEPENDS
    LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
