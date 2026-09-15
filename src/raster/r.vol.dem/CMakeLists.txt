cmake_minimum_required(VERSION 3.22)

project(r.vol.dem)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    chull.c
    chull.h
    globals.h
    macros.h
    main.c
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  DOCFILES
    r_vol_dem_layerdown.jpg
    r_vol_dem_layerup.jpg
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
