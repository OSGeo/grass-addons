cmake_minimum_required(VERSION 3.22)

project(i.evapo.potrad)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES
    et_pot_day.c
    main.c
    r_net_day_bandara98.c
    r_net_day.c
    solar_day_3d.c
    solar_day.c
  GRASSLIBS
    gis
    raster
  DEPENDS LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
