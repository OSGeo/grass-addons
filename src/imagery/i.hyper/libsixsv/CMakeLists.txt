cmake_minimum_required(VERSION 3.22)

project(libsixsv)

include(build_addon)

set(sources
  src/adjacency.c
  src/aeroprof.c
  src/aerosol_tables.c
  src/aerosol.c
  src/atcorr.c
  src/atmosphere.c
  src/brdf.c
  src/chand.c
  src/correct.c
  src/csalbr.c
  src/discom.c
  src/discre.c
  src/enviro.c
  src/gas_abs.c
  src/gas_tables.c
  src/gauss.c
  src/interp.c
  src/kernel.c
  src/kernelpol.c
  src/lut.c
  src/mie.c
  src/oe_invert.c
  src/ospol.c
  src/polglit.c
  src/possol.c
  src/pressure.c
  src/rayleigh.c
  src/retrieve.c
  src/rt.c
  src/scatra.c
  src/solar_table.c
  src/solar.c
  src/spatial.c
  src/spectral_brdf.c
  src/srf_conv.c
  src/surface_model.c
  src/terrain.c
  src/trunca.c
  src/uncertainty.c)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  HEADERS
    include/adjacency.h
    include/aerosol_tables.h
    include/atcorr.h
    include/brdf.h
    include/gas_tables.h
    include/oe_invert.h
    include/retrieve.h
    include/sixs_ctx.h
    include/solar_table.h
    include/spatial.h
    include/spectral_brdf.h
    include/surface_model.h
    include/terrain.h
    include/uncertainty.h
  GRASSLIBS
    gis)

target_include_directories(${PROJECT_NAME}
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>)
