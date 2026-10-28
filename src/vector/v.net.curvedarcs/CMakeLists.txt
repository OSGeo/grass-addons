cmake_minimum_required(VERSION 3.22)

project(v.net.curvedarcs)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    v_net_curvedarcs.png
    v_net_curvedarcs2.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
