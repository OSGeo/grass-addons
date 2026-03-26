cmake_minimum_required(VERSION 3.22)

project(r.connectivity LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.connectivity.corridors
    r.connectivity.distance
    r.connectivity.network
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
