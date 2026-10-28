cmake_minimum_required(VERSION 3.22)

project(r.colors.qml)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.colors.qml.py
  DOCFILES r.colors.qml.html r.colors.qml.md r_colors_qml.png)
