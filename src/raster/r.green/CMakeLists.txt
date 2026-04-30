cmake_minimum_required(VERSION 3.22)

project(r.green LANGUAGES NONE)

include(build_addon)

add_subdirectory(libgreen)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.green.biomassfor
    r.green.gshp
    r.green.hydro
    r.green.install
  DOCFILES
    r_green.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
