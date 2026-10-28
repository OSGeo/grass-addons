cmake_minimum_required(VERSION 3.22)

project(v.net.salesman.opt)

include(build_addon)

set(sources
  evolution.c
  local_proto.h
  main.c
  optimize.c
  tour.c)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    vector
  SOURCES ${sources}
  DOCFILES
    v.net.salesman.opt.html
    v.net.salesman.opt.md
    vnetsalesman.png
    vnetsalesmantime.png)
