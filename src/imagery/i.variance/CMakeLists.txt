cmake_minimum_required(VERSION 3.22)

project(i.variance LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i_variance_region1.png
    i_variance_region2.png
    i_variance_region3.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
