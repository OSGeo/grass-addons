cmake_minimum_required(VERSION 3.22)

project(r.vif LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_vif_example1.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
