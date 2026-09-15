cmake_minimum_required(VERSION 3.22)

project(r.in.ahn.laz LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_in_ahn_01.png
    r_in_ahn_02.png
    r_in_ahn_03.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
