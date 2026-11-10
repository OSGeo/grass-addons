cmake_minimum_required(VERSION 3.22)

project(t.rast.boxplot LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    t_rast_boxplot_01.png
    t_rast_boxplot_02.png
    t_rast_boxplot_03.png
    t_rast_boxplot_04.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
