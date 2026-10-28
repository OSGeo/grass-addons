cmake_minimum_required(VERSION 3.22)

project(r.valley.bottom LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_valley_bottom_mrvbf.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
