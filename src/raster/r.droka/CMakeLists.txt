cmake_minimum_required(VERSION 3.22)

project(r.droka LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_droka_img.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
