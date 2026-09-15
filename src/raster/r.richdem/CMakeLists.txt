cmake_minimum_required(VERSION 3.22)

project(r.richdem LANGUAGES NONE)

include(build_addon)

add_subdirectory(librichdem)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.richdem.filldepressions
    r.richdem.breachdepressions
    r.richdem.resolveflats
    r.richdem.flowaccumulation
    r.richdem.terrainattribute
    r.richdem.dephier
    r.richdem.fsm
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
