cmake_minimum_required(VERSION 3.22)

project(r.forestfrag LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_forestfrag_window_11.png
    r_forestfrag_window_7.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
