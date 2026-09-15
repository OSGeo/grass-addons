cmake_minimum_required(VERSION 3.22)

project(r.out.legend LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_out_legend_1.png
    r_out_legend_2.png
    r_out_legend_3.png
    r_out_legend_4.png
    r_out_legend_5.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
