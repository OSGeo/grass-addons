cmake_minimum_required(VERSION 3.22)

project(v.build.pg)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.build.pg.py
  DOCFILES
    v.build.pg.html
    v.build.pg.md)
