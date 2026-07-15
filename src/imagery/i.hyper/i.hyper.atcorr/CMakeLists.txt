cmake_minimum_required(VERSION 3.22)

project(i.hyper.atcorr)

include(build_addon)
find_M()
find_OpenMP()

set(sixsv_src
  ../libsixsv/src/adjacency.c
  ../libsixsv/src/aeroprof.c
  ../libsixsv/src/aerosol.c
  ../libsixsv/src/aerosol_tables.c
  ../libsixsv/src/atcorr.c
  ../libsixsv/src/atmosphere.c
  ../libsixsv/src/brdf.c
  ../libsixsv/src/chand.c
  ../libsixsv/src/correct.c
  ../libsixsv/src/csalbr.c
  ../libsixsv/src/discom.c
  ../libsixsv/src/discre.c
  ../libsixsv/src/enviro.c
  ../libsixsv/src/gas_abs.c
  ../libsixsv/src/gas_tables.c
  ../libsixsv/src/gauss.c
  ../libsixsv/src/interp.c
  ../libsixsv/src/kernel.c
  ../libsixsv/src/kernelpol.c
  ../libsixsv/src/lut.c
  ../libsixsv/src/mie.c
  ../libsixsv/src/oe_invert.c
  ../libsixsv/src/ospol.c
  ../libsixsv/src/polglit.c
  ../libsixsv/src/possol.c
  ../libsixsv/src/pressure.c
  ../libsixsv/src/rayleigh.c
  ../libsixsv/src/retrieve.c
  ../libsixsv/src/rt.c
  ../libsixsv/src/scatra.c
  ../libsixsv/src/solar.c
  ../libsixsv/src/solar_table.c
  ../libsixsv/src/spatial.c
  ../libsixsv/src/spectral_brdf.c
  ../libsixsv/src/srf_conv.c
  ../libsixsv/src/surface_model.c
  ../libsixsv/src/terrain.c
  ../libsixsv/src/trunca.c
  ../libsixsv/src/uncertainty.c)

set(addon_sources main.c ${sixsv_src})

build_addon(
  ${PROJECT_NAME}
  SOURCES ${addon_sources}
  GRASSLIBS
    gis
    raster
    raster3d
  DEPENDS
    LIBM
  OPTIONAL_DEPENDS
    OpenMP::OpenMP_C
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)

target_include_directories(${PROJECT_NAME} PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/../libsixsv/include>
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/../libsixsv/src>)

target_compile_options(${PROJECT_NAME} PRIVATE -O3 -ffast-math)
