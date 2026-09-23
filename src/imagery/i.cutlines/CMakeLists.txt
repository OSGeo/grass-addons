cmake_minimum_required(VERSION 3.22)

project(i.cva LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i.cva_1angle.png
    i.cva_2angleclass.png
    i.cva_3magnitude.png
    i.cva_4change.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
