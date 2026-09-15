cmake_minimum_required(VERSION 3.22)

project(r.change.info)

include(build_addon)

find_M()

set(sources
  bufs.c
  chisq.c
  dist.c
  gain.c
  gather.c
  gini.c
  local_proto.h
  main.c
  ncb.h
  null_cats.c
  ratio.c
  readcell.c
  window.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
