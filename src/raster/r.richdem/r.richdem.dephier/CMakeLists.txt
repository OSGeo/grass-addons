cmake_minimum_required(VERSION 3.22)

project(r.richdem.dephier LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md
    esurf-9-105-2021-f02.png
    esurf-8-431-2020-f01.png
    esurf-8-431-2020-f09.png)
