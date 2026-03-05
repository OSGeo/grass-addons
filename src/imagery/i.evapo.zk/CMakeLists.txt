cmake_minimum_required(VERSION 3.22)

project(i.evapo.zk)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    main.c
    zk_daily_et.c
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
