cmake_minimum_required(VERSION 3.22)

project(r.earthworks LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_earthworks_01.png
    r_earthworks_02.png
    r_earthworks_03.png
    r_earthworks_04.png
    r_earthworks_05.png
    r_earthworks_06.png
    r_earthworks_07.png
    r_earthworks_08.png
    r_earthworks_09.png
    r_earthworks_10.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
