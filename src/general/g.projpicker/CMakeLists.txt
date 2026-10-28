cmake_minimum_required(VERSION 3.22)

project(g.projpicker LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    g_projpicker_gui.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
