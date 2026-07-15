cmake_minimum_required(VERSION 3.22)

project(r.maxent.train LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_maxent_train_01.png
    r_maxent_train_02.png
    r_maxent_train_workflow.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
