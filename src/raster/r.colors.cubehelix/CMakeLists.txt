cmake_minimum_required(VERSION 3.22)

project(r.colors.cubehelix LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_colors_cubehelix_two_colors.png
    r_colors_cubehelix.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
