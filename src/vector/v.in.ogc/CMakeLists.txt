cmake_minimum_required(VERSION 3.22)

project(v.in.ogc)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    v.in.ogc.features
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
