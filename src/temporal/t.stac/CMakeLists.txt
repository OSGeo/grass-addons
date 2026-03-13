cmake_minimum_required(VERSION 3.22)

project(t.stac LANGUAGES NONE)

include(build_addon)

add_subdirectory(libstac)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    t.stac.catalog
    t.stac.collection
    t.stac.item
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
