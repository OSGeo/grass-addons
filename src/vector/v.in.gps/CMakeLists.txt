cmake_minimum_required(VERSION 3.22)

project(v.in.gps)

include(build_addon)

add_files_to_etc_dir(${PROJECT_NAME} FILES grass_write_ascii.style)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
