cmake_minimum_required(VERSION 3.22)

project(v.multi2singlepart)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    example.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
