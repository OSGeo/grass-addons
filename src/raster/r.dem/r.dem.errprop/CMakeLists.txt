cmake_minimum_required(VERSION 3.22)

project(r.dem.errprop LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md
    r_dem_errprop_classes.png)
