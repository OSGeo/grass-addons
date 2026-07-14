cmake_minimum_required(VERSION 3.22)

project(r.series.boxplot LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_series_boxplot_1.png
    r_series_boxplot_2.png
    r_series_boxplot_3.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
