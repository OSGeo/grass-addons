cmake_minimum_required(VERSION 3.22)

project(i.modis LANGUAGES NONE)

include(build_addon)

add_subdirectory(libmodis)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    i.modis.download
    i.modis.import
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
