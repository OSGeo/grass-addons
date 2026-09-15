cmake_minimum_required(VERSION 3.22)

project(i.landsat)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    i.landsat.download
    i.landsat.import
    i.landsat.qa
  DOCFILES
    i.landsat.html
    i.landsat.md)
