cmake_minimum_required(VERSION 3.22)

project(v.in.survey)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    img_lyrs_broken.png
    img_NC_dxf.png
    img_soils_correct.png
    img_sorted_boundaries.png
    v.in.survey.html
    v.in.survey.md)
