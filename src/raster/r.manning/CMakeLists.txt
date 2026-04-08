cmake_minimum_required(VERSION 3.22)

project(r.manning)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.manning.py
  DOCFILES r.manning.html r.manning.md r_manning.png)
