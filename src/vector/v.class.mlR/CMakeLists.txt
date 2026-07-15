cmake_minimum_required(VERSION 3.22)

project(v.class.mlR)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.class.mlR.py
  DOCFILES
    v.class.mlR.html
    v.class.mlR.md)
