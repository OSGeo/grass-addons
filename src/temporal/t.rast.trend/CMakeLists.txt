cmake_minimum_required(VERSION 3.22)

project(t.rast.trend LANGUAGES NONE)

include(build_addon)

add_subdirectory(trendlib)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    t.rast.stl
    t.rast.stl2ca
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
