cmake_minimum_required(VERSION 3.22)

project(r.viewshed.exposure LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_viewshed_exposure_example_binary.png
    r_viewshed_exposure_example_solid_angle.png
    r_viewshed_exposure_workflow.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
