cmake_minimum_required(VERSION 3.22)

project(r.skyline)

include(build_addon)

set(sources
    azimuth.c
    file.c
    find_edges.c
    find_horizon.c
    list.c
    main.c
    raster_file.c
    skyline.c
    sort.c)

set(doc_files
   r.skyline.html
   r.skyline.md)

build_addon(${PROJECT_NAME}
  GRASSLIBS gis raster
  SOURCES ${sources}
  DOCFILES ${doc_files})
