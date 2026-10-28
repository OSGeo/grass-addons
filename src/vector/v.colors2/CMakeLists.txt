cmake_minimum_required(VERSION 3.22)

project(v.colors2)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.colors2.py
  DOCFILES
    v.colors2.html
    v.colors2.md)
