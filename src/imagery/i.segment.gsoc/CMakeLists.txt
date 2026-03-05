cmake_minimum_required(VERSION 3.22)

project(i.segment.gsoc)

include(build_addon)

find_M()

set(sources
  create_isegs.c
  estimate_threshold.c
  flag.c
  flag.h
  iseg.h
  main.c
  open_files.c
  parse_args.c
  write_output.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    btree2
    gis
    imagery
    linkm
    raster
    segment
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
