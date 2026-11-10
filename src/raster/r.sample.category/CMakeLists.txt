cmake_minimum_required(VERSION 3.22)

project(r.sample.category LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r.sample.category.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
