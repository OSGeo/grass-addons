cmake_minimum_required(VERSION 3.22)

project(v.lidar.mcc)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    v_lidar_mcc.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
