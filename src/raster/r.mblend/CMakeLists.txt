cmake_minimum_required(VERSION 3.22)

project(r.mblend LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    blended.png
    both_inputs.png
    edges.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
