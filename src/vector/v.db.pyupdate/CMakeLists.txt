cmake_minimum_required(VERSION 3.22)

project(v.db.pyupdate)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.db.pyupdate.py
  DOCFILES
    v.db.pyupdate.html
    v.db.pyupdate.md)
