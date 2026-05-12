project(r.futures.simulation)

include(build_addon)

find_M()

set(sources
  climate.c
  climate.h
  devpressure.c
  devpressure.h
  inputs.c
  inputs.h
  main.c
  map.c
  map.h
  output.c
  output.h
  patch.c
  patch.h
  random.c
  random.h
  redistribute.c
  redistribute.h
  simulation.c
  simulation.h
  utils.c
  utils.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    datetime
    gis
    raster
    segment
  DEPENDS
    LIBM
  DOCFILES
    incentive.png
    r_futures_detail.png
    r_futures_scenario_infill.png
    r_futures_scenario_sprawl.png
    r_futures_scenario_status_quo.png
    r_futures.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
