cmake_minimum_required(VERSION 3.22)

project(v.convert.all)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.convert.all.py
  DOCFILES
    v.convert.all.html
    v.convert.all.md)
