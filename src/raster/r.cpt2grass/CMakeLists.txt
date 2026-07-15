cmake_minimum_required(VERSION 3.22)

project(r.cpt2grass LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_cpt2grass_color_table_DEM_screen.png
    r_cpt2grass_color_table_YlOrBr_09.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
