cmake_minimum_required(VERSION 3.22)

project(v.explode)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.explode.py
  DOCFILES
    v.explode.html
    v.explode.md)
