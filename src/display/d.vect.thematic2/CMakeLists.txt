cmake_minimum_required(VERSION 3.22)

project(d.vect.thematic2 LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    d_vect_thematic_equake.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
