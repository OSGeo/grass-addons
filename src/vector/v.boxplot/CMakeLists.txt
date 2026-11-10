cmake_minimum_required(VERSION 3.22)

project(v.boxplot)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.boxplot.py
  DOCFILES
    v_boxplot_01.png
    v_boxplot_02.png
    v.boxplot.html
    v.boxplot.md)
