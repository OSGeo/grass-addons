cmake_minimum_required(VERSION 3.22)

project(r.maxent.predict LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_maxent_predict_01.png
    r_maxent_predict_02.png
    r_maxent_predict_workflow.png
    r_maxent_train.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
