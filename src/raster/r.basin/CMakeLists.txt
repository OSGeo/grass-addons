cmake_minimum_required(VERSION 3.22)

project(r.basin LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_basin_map.png
    r_basin1.png
    r_basin2.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
