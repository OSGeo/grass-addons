cmake_minimum_required(VERSION 3.22)

project(v.scatterplot)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    v_scatterplot_01.png
    v_scatterplot_02.png
    v_scatterplot_03.png
    v_scatterplot_04.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
