cmake_minimum_required(VERSION 3.22)

project(i.sentinel)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    i.sentinel.coverage
    i.sentinel.download
    i.sentinel.import
    i.sentinel.mask
    i.sentinel.parallel.download
    i.sentinel.preproc
  DOCFILES
    i.sentinel.html
    i.sentinel.md)
