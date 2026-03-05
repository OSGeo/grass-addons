cmake_minimum_required(VERSION 3.22)
project(r.accumulate)

include(build_addon)

find_OpenMP()
find_M()

set(sources
    accumulate_iterative.c
    accumulate_recursive.c
    calculate_lfp_iterative.c
    calculate_lfp_recursive.c
    delineate_streams.c
    delineate_subwatersheds_iterative.c
    delineate_subwatersheds_recursive.c
    global.h
    line_list.c
    point_list.c
    main.c
    raster.c
    subaccumulate.c)

set(doc_files
    r.accumulate.html
    r.accumulate.md
    r_accumulate_formats.png
    r_accumulate_nc_comparison.png
    r_accumulate_nc_example.png
    r_accumulate_nc_lfp_example_multiple.png
    r_accumulate_nc_lfp_example_single.png
    r_accumulate_nc_lfp_example_subwatersheds.png
    r_accumulate_nc_stream_comparison.png
    r_accumulate_nc_stream_example.png
    r_accumulate_nc_subwatersheds_example.png
    r_accumulate_nc_watershed_example.png
    r_accumulate_r_watershed_nc_example.png)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    raster
    vector
  DEPENDS
    LIBM
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C
  SOURCES ${sources}
  DOCFILES ${doc_files})
