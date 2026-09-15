cmake_minimum_required(VERSION 3.22)

project(r.slopeunits LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.slopeunits.clean
    r.slopeunits.create
    r.slopeunits.metrics
    r.slopeunits.optimize
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
