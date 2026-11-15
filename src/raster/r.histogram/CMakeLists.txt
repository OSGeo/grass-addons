cmake_minimum_required(VERSION 3.22)

project(r.histogram LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_histogram_01.png
    r_histogram_02.png
    r_histogram_03.png
    r_histogram_04.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
