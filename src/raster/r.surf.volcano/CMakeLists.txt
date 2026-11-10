cmake_minimum_required(VERSION 3.22)

project(r.surf.volcano LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_surf_volcano_gaussian.jpg
    r_surf_volcano_volcano3D.jpg
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
