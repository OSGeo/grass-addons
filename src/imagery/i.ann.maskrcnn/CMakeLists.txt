cmake_minimum_required(VERSION 3.22)

project(i.ann.maskrcnn LANGUAGES NONE)

include(build_addon)

add_subdirectory(maskrcnnlib)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    i.ann.maskrcnn.detect
    i.ann.maskrcnn.train
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
