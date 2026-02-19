cmake_minimum_required(VERSION 3.22)
project(r.curvenumber)

include(build_addon)

find_M()

set(sources
    lut.c
    main.c)

set(doc_files
    r.curvenumber.html
    r.curvenumber.md
    r_curvenumber_output.png)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    dbmidriver
    gmath
    gis
    raster
    vector
  DEPENDS
    LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
