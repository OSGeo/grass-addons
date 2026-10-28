cmake_minimum_required(VERSION 3.22)

project(r.out.kde LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_out_kde.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
