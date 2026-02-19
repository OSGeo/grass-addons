cmake_minimum_required(VERSION 3.22)
project(r.timeofconcentration)

include(build_addon)

set(doc_files
    r.timeofconcentration.html
    r.timeofconcentration.md
    tc_nc.png)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    r.timeofconcentration.py
  DOCFILES ${doc_files})
