cmake_minimum_required(VERSION 3.22)

project(i.lmf)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    fitting.c
    invert_matrix.c
    lmf.c
    main.c
    make_matrix.c
    maxmin.c
    minmax.c
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
