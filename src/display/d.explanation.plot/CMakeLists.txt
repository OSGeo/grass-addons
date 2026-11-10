cmake_minimum_required(VERSION 3.22)

project(d.explanation.plot LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    d_explanation_plot_with_r_series.png
    d_explanation_plot.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
