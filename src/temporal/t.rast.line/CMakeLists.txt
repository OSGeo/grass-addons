cmake_minimum_required(VERSION 3.22)

project(t.rast.line LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    t_rast_line_0.png
    t_rast_line_01.png
    t_rast_line_02.png
    t_rast_line_03.png
    t_rast_line_04.png
    t_rast_line_04b.png
    t_rast_line_04c.png
    t_rast_line_05.png
    t_rast_line_06.png
    t_rast_line_07.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
