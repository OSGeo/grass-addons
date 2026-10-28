cmake_minimum_required(VERSION 3.22)

project(r.lake.series LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r.lake.series.jpg
    rural_flooding_105.jpg
    rural_flooding_108.jpg
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
