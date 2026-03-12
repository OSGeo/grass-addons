cmake_minimum_required(VERSION 3.22)

project(v.clean.ogr)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.clean.ogr.py
  DOCFILES
    v.clean.ogr.html
    v.clean.ogr.md)
