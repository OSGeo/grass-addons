cmake_minimum_required(VERSION 3.22)

project(i.hyper)

include(build_addon)

add_subdirectory(i_hyper_lib)
add_subdirectory(libsixsv)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    i.hyper.atcorr
    i.hyper.composite
    i.hyper.explore
    i.hyper.export
    i.hyper.import
    i.hyper.metadata
    i.hyper.preproc
    i.hyper.specresamp
  DOCFILES
    i.hyper.html
    i.hyper.md)
