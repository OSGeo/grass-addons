cmake_minimum_required(VERSION 3.22)

project(v.histogram)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.histogram.py
  DOCFILES
    v_histogram_01.png
    v_histogram_02.png
    v.histogram.html
    v.histogram.md)
