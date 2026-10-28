cmake_minimum_required(VERSION 3.22)

project(r.out.3mf)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.out.3mf.py
  DOCFILES
    r.out.3mf.html
    r.out.3mf.md)
