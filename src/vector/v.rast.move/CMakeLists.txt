cmake_minimum_required(VERSION 3.22)

project(v.rast.move)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    v_rast_move.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
