cmake_minimum_required(VERSION 3.22)

project(v.delaunay3d)

include(build_addon)

find_package(CGAL REQUIRED)

set(sources
  local_proto.h
  main.cpp
  read.cpp
  write.cpp)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    vector
  DEPENDS
    CGAL::CGAL
  SOURCES ${sources}
  DOCFILES
    v.delaunay3d.html
    v.delaunay3d.md)
