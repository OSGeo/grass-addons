cmake_minimum_required(VERSION 3.22)

project(r.gravity.terrain LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_gravity_terrain.png
    TC_compare.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
