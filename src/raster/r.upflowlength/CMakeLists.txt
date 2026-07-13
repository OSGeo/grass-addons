cmake_minimum_required(VERSION 3.22)

project(r.upflowlength)

include(build_addon)

find_OpenMP()
find_M()

set(sources
    gettimeofday.c
    global.h
    main.c
    raster_io.c
    timeval_diff.c
    uflen_funcs.h)

set(doc_files
    r_upflowlength_custom_formats.png
    r_upflowlength_elevation_example.png
    r_upflowlength_elev_state_500m_example.png
    r_upflowlength_formats.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster
  DEPENDS
    LIBM
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C
  SOURCES ${sources}
  DOCFILES ${doc_files})
