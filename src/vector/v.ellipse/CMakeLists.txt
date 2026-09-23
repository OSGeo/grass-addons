cmake_minimum_required(VERSION 3.22)

project(v.ellipse)

include(build_addon)

find_M()

set(sources
  ellipse.c
  main.c
  proto.h
  read.c
  write.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    gis
    gmath
    vector
  DEPENDS
    LIBM
  SOURCES ${sources}
  DOCFILES
    v_ellipse.png
    v.ellipse.html
    v.ellipse.md)
