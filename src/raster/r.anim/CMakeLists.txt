cmake_minimum_required(VERSION 3.22)

project(r.anim LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.anim.morph
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
