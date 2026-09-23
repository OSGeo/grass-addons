cmake_minimum_required(VERSION 3.22)

project(v.concave.hull)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.concave.hull.py
  DOCFILES
    v_concave_alpha_0_5.png
    v_concave_alpha_8.png
    v_concave_concave.png
    v_concave_convex.png
    v.concave.hull.html
    v.concave.hull.md)
