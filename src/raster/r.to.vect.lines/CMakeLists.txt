cmake_minimum_required(VERSION 3.22)

project(r.to.vect.lines LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_to_vect_lines_example.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
