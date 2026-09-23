cmake_minimum_required(VERSION 3.22)

project(r3.profile)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
    raster3d
    vector
  DEPENDS
    LIBM
  SOURCES
    double_list.c
    double_list.h
    input.c
    local_proto.h
    main.c
    read_rast.c
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
