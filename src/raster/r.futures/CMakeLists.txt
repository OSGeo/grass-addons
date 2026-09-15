cmake_minimum_required(VERSION 3.22)

project(r.futures LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.futures.calib
    r.futures.demand
    r.futures.devpressure
    r.futures.gridvalidation
    r.futures.parallelpga
    r.futures.pga
    r.futures.potential
    r.futures.potsurface
    r.futures.simulation
    r.futures.validation
  DOCFILES
    FUTURES_inputs_diagram.png
    r_futures_ncsmp.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
