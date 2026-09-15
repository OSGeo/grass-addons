cmake_minimum_required(VERSION 3.22)

project(r.learn.ml2 LANGUAGES NONE)

include(build_addon)

add_subdirectory(rlearnlib)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.learn.predict
    r.learn.train
  DOCFILES
    lsat7_2000_b742.png
    rfclassification.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
