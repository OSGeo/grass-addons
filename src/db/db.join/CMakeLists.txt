cmake_minimum_required(VERSION 3.22)

project(db.join)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    db.join.py
  DOCFILES
    db.join.html
    db.join.md)
