cmake_minimum_required(VERSION 3.22)

project(v.stats)

include(build_addon)

add_files_to_etc_dir(${PROJECT_NAME} FILES imp_csv.py vstats.py)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
