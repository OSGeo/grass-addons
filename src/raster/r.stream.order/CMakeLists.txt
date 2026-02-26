cmake_minimum_required(VERSION 3.22)

project(r.stream.order)

include(build_addon)

find_M()

set(sources
    io.c
    io.h
    local_proto.h
    local_vars.h
    main.c
    stream_init.c
    stream_order.c
    stream_raster_close.c
    stream_topology.c
    stream_vector.c)

set(doc_files
    r.stream.order.html
    r.stream.order.md
    orders.png)

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
