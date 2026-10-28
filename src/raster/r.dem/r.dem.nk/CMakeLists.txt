cmake_minimum_required(VERSION 3.22)

project(r.dem.nk)

include(build_addon)

find_M()

set(sources
    main.c)

set(doc_files
    r.dem.nk.html
    r.dem.nk.md
    r_dem_nk_convergence.png)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS gis raster
  SOURCES ${sources}
  DOCFILES ${doc_files}
  DEPENDS
    LIBM)
