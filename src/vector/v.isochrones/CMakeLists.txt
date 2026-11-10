cmake_minimum_required(VERSION 3.22)

project(v.isochrones)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    v_isochrones_cost.png
    v_isochrones_net.png
    v.isochrones.html
    v.isochrones.md)
