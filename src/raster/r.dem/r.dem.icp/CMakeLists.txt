cmake_minimum_required(VERSION 3.22)

project(r.dem.icp)

include(build_addon)

find_OpenMP()
find_M()

set(sources
    icp.c
    linalg.c
    main.c
    normals.c
    resample.c
    utils.c)

set(doc_files
    r.dem.icp.html
    r.dem.icp.md
    r_dem_icp_alignment.png)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS gis raster
  SOURCES ${sources}
  DOCFILES ${doc_files}
  DEPENDS
    LIBM
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C)
