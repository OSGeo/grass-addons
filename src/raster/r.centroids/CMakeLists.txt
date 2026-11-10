cmake_minimum_required(VERSION 3.22)

project(r.centroids LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_centroids_basin_50K.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
