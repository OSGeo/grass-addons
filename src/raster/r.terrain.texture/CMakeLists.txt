cmake_minimum_required(VERSION 3.22)

project(r.terrain.texture LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    classification_example.png
    convexity_example.png
    flowchart.png
    texture_example.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
