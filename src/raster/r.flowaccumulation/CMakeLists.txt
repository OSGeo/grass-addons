cmake_minimum_required(VERSION 3.22)

project(r.flowaccumulation)

include(build_addon)

find_M()

set(sources
    accumulate_c.c
    accumulate_cm.c
    accumulate_cmw.c
    accumulate_cmz.c
    accumulate_co.c
    accumulate_com.c
    accumulate_comz.c
    accumulate_coz.c
    accumulate_cw.c
    accumulate_cz.c
    accumulate_d.c
    accumulate_dm.c
    accumulate_dmw.c
    accumulate_dmz.c
    accumulate_do.c
    accumulate_dom.c
    accumulate_domz.c
    accumulate_doz.c
    accumulate_dw.c
    accumulate_dz.c
    accumulate_f.c
    accumulate_fm.c
    accumulate_fmw.c
    accumulate_fmz.c
    accumulate_fo.c
    accumulate_fom.c
    accumulate_fomz.c
    accumulate_foz.c
    accumulate_funcs.h
    accumulate_fw.c
    accumulate_fz.c
    accumulate.c
    gettimeofday.c
    main.c
    timeval_diff.c)

set(doc_files
    r.flowaccumulation.html
    r.flowaccumulation.md
    r_flowaccumulation_formats.png
    r_flowaccumulation_nc_comparison.png
    r_flowaccumulation_nc_example.png
    r_flowaccumulation_r_watershed_nc_example.png)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS gis raster
  DEPENDS LIBM
  SOURCES ${sources}
  DOCFILES ${doc_files})
