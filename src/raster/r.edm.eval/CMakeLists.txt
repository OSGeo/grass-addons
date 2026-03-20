cmake_minimum_required(VERSION 3.22)

project(r.edm.eval LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_edm_eval_01.png
    r_edm_eval_02.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
