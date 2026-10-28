cmake_minimum_required(VERSION 3.22)

project(r.hypso)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.hypso.py
  DOCFILES r.hypso.html r.hypso.md)
