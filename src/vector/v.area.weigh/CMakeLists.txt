cmake_minimum_required(VERSION 3.22)

project(v.area.weigh)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.area.weigh.py
  DOCFILES
    v.area.weigh.html
    v.area.weigh.md)
