cmake_minimum_required(VERSION 3.22)

project(r.in.ogc LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.in.ogc.coverages
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
