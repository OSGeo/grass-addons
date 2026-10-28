cmake_minimum_required(VERSION 3.22)

project(r.slope.direction LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_slope_direction_fdir_slope_1.png
    r_slope_direction_fdir_slope_13.png
    r_slope_direction_fdir_slope_5.png
    r_slope_direction_streets_wake_slope_1.png
    r_slope_direction_streets_wake_slope_13.png
    r_slope_direction_streets_wake_slope_5.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
