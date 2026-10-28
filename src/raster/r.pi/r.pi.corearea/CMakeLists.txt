project(r.pi.corearea)

include(build_addon)

find_M()

set(sources
  func.c
  local_proto.h
  main.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
    stats
  DEPENDS
    LIBM
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
