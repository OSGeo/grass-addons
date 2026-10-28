cmake_minimum_required(VERSION 3.22)

project(r.in.nasadem LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_in_nasadem_etna.jpg
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
