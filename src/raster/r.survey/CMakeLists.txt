cmake_minimum_required(VERSION 3.22)

project(r.survey LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_survey_fig_2.png
    r_survey_view_angle.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
