cmake_minimum_required(VERSION 3.22)

project(r.series.lwr)

include(build_addon)

find_M()

build_addon(
  ${PROJECT_NAME}
  SOURCES main.c
  GRASSLIBS
    gis
    gmath
    raster
  DEPENDS
    LIBM
  DOCFILES
    r_series_lwr_cla_201281.png
    r_series_lwr_cla_lwr1_lwr2.png
    r_series_lwr_cla_lwr3_lwr4.png
    r_series_lwr_cla_lwr7_201281.png
    r_series_lwr_cla_orig_lwr5.png
    r_series_lwr_cla_orig.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
