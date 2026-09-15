cmake_minimum_required(VERSION 3.22)

project(r.seasons)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES main.c
  GRASSLIBS
    gis
    raster
  DOCFILES
    global_ndvi.png
    ndvi_season2_end1.png
    ndvi_season2_start1.png
    number_seasons_ndvi.png
    time_series_ndvi.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
