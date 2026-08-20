cmake_minimum_required(VERSION 3.22)

project(v.photo.geometry LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    v_photo_geometry.png
    v_photo_geometry_density.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
