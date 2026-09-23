cmake_minimum_required(VERSION 3.22)

project(r.landscape.evol.old LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_landscape_evol_equation1.png
    r_landscape_evol_equation2.png
    r_landscape_evol_equation3.png
    r_landscape_evol_equation4.png
    r_landscape_evol_equation5.png
    r_landscape_evol_equation6.png
    r_landscape_evol_Flow_acc_vs_curvature.png
    r_landscape_evol_Map1.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
