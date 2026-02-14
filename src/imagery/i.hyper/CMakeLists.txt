cmake_minimum_required(VERSION 3.22)

project(i.hyper)

include(build_addon)

add_subdirectory(i_hyper_lib)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    i.hyper.composite
    i.hyper.explore
    i.hyper.export
    i.hyper.import
    i.hyper.preproc
  DOCFILES
    i.hyper.html
    i.hyper.md)
