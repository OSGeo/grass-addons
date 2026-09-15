cmake_minimum_required(VERSION 3.22)

project(v.profile.points)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    v_profile_points_workspace.png
    v_profile_points.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
