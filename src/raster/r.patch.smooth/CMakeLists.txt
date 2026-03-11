cmake_minimum_required(VERSION 3.22)

project(r.patch.smooth LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_patch_smooth_overview.png
    r_patch_smooth_parallel_smoothing.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
