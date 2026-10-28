cmake_minimum_required(VERSION 3.22)

project(r.shaded.pca LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r.shaded.pca.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
