cmake_minimum_required(VERSION 3.22)

project(i.histo.match LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i_histo_match_matched.png
    i_histo_match_original.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
