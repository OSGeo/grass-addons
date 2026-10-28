cmake_minimum_required(VERSION 3.22)

project(i.sam2 LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i_sam2_trees.jpg
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
