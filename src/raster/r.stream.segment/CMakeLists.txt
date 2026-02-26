cmake_minimum_required(VERSION 3.22)

project(r.stream.segment)

include(build_addon)

find_M()

set(sources
    io.c
    io.h
    local_proto.h
    local_vars.h
    main.c
    stream_segment.c
    stream_topology.c
    stream_vector.c
)

set(doc_files
    r.stream.segment.html
    r.stream.segment.md
    dirs.png
    sectors.png)

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
