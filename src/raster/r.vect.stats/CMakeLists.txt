cmake_minimum_required(VERSION 3.22)

project(r.vect.stats LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_to_vect_schools_count.png
    r_to_vect_schools_sum.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
