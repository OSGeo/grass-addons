cmake_minimum_required(VERSION 3.22)

project(r.stream.stats)

include(build_addon)

find_M()

set(sources
    io.c
    io.h
    local_proto.h
    local_vars.h
    main.c
    stats_calculate.c
    stats_prepare.c
    stats_print.c)

set(doc_files
    r.stream.stats.html
    r.stream.stats.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
    segment
  DEPENDS
    LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
