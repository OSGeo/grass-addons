cmake_minimum_required(VERSION 3.22)

project(r.colors.toqml)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.colors.toqml.py
  DOCFILES r.colors.toqml.html r.colors.toqml.md r_colors_toqml.png)
