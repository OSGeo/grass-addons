cmake_minimum_required(VERSION 3.22)

project(v.external.all)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.external.all.py
  DOCFILES
    v.external.all.html
    v.external.all.md)
