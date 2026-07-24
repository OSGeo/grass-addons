cmake_minimum_required(VERSION 3.22)

project(v.faultdirections)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.faultdirections.py
  DOCFILES
    v.faultdirections.html
    v.faultdirections.md)
