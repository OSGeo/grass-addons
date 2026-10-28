cmake_minimum_required(VERSION 3.22)

project(v.in.wfs2)

include(build_addon)

add_files_to_etc_dir(
  ${PROJECT_NAME}
  FILES
    wfs_base.py
    wfs_drv.py
    wfs_owslib_drv.py)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
