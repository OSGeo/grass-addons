cmake_minimum_required(VERSION 3.22)

project(r.roughness.vector)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.roughness.vector.py
  DOCFILES r.roughness.vector.html r.roughness.vector.md)
