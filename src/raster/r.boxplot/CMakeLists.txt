cmake_minimum_required(VERSION 3.22)

project(r.boxplot LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_boxplot_01.png
    r_boxplot_02.png
    r_boxplot_03.png
    r_boxplot_04.png
    r_boxplot_05.png
    r_boxplot_06.png
    r_boxplot_map_03.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
