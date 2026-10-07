cmake_minimum_required(VERSION 3.22)

project(i.cutlines LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i_cutlines_canny.png
    i_cutlines_default.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
