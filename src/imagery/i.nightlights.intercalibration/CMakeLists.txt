cmake_minimum_required(VERSION 3.22)

project(i.nightlights.intercalibration LANGUAGES NONE)

include(build_addon)

add_files_to_etc_dir(
  ${PROJECT_NAME}
  FILES
    intercalibration_coefficients.py
    intercalibration_equations.py
    intercalibration_models.py)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
