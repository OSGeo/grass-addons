cmake_minimum_required(VERSION 3.22)

project(r.tpi)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.tpi.py
  DOCFILES r.tpi.html r.tpi.md r_tpi.png)
