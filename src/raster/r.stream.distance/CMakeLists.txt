cmake_minimum_required(VERSION 3.22)

project(r.stream.distance)

include(build_addon)

set(sources
    distance_calc.c
    distance_init.c
    io.c
    main.c)

set(doc_files
    r.stream.distance.html
    r.stream.distance.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS gis raster segment
  SOURCES ${sources}
  DOCFILES ${doc_files})
