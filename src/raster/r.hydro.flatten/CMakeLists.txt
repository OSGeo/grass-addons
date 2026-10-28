cmake_minimum_required(VERSION 3.22)

project(r.hydro.flatten LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_hydro_flatten_input.png
    r_hydro_flatten_output_elevation.png
    r_hydro_flatten_output_stddev.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
