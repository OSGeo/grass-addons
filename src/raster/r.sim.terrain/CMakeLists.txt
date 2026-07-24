cmake_minimum_required(VERSION 3.22)

project(r.sim.terrain LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_sim_terrain_rusle.png
    r_sim_terrain.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
