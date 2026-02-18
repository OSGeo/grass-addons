cmake_minimum_required(VERSION 3.22)

project(v.in.redwg)

include(build_addon)

find_M()

find_package(PkgConfig QUIET)
pkg_check_modules(LibreDWG libredwg REQUIRED)
if(LibreDWG_FOUND)
  set(_LibreDWG_link_dirs "${LibreDWG_LIBDIR}" "${LibreDWG_LIBRARY_DIRS}")
  list(REMOVE_DUPLICATES _LibreDWG_link_dirs)
  find_library(LibreDWG_Library NAMES redwg PATHS ${LibreDWG_LIBDIR})
  add_library(LibreDWG::LibreDWG UNKNOWN IMPORTED)
  set_target_properties(
    LibreDWG::LibreDWG
    PROPERTIES IMPORTED_LOCATION "${LibreDWG_Library}"
               INTERFACE_INCLUDE_DIRECTORIES "${LibreDWG_INCLUDE_DIRS}"
               INTERFACE_LINK_LIBRARIES "${LibreDWG_LINK_LIBRARIES}"
               INTERFACE_LINK_DIRECTORIES "${_LibreDWG_link_dirs}")
endif()

set(sources
  entity.c
  global.h
  main.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    dbmibase
    dbmiclient
    gis
    vector
  SOURCES ${sources}
  DEPENDS
    LIBM
    LibreDWG::LibreDWG
  DOCFILES
    v.in.redwg.html
    v.in.redwg.md)
