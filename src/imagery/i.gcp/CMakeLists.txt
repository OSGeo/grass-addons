cmake_minimum_required(VERSION 3.22)

project(i.gcp)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    main.c
    points.c
  GRASSLIBS
    gis
    imagery
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
