cmake_minimum_required(VERSION 3.22)

project(v.transects)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    vtransect_options1.jpg
    vtransect_options2.jpg
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
