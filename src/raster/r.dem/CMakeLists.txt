cmake_minimum_required(VERSION 3.22)

project(r.dem LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.dem.bias
    r.dem.change
    r.dem.coregister
    r.dem.errprop
    r.dem.icp
    r.dem.lod
    r.dem.nk
    r.dem.screen
    r.dem.stats
  DOCFILES
    r.dem.html
    r.dem.md)
