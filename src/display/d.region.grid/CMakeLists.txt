cmake_minimum_required(VERSION 3.22)

project(d.region.grid)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES d.region.grid.py
  DOCFILES
    d_region_grid_new_region_grid.png
    d_region_grid_two_rasters.png
    d.region.grid.html
    d.region.grid.md)
