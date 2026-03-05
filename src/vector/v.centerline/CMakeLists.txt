cmake_minimum_required(VERSION 3.22)

project(v.centerline)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.centerline.py
  DOCFILES
    v_centerline_flightpaths.png
    v_centerline_river.png
    v.centerline.html
    v.centerline.md)
