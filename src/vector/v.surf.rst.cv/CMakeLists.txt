cmake_minimum_required(VERSION 3.22)

project(v.surf.rst.cv)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.surf.rst.cv.py
  DOCFILES
    v.surf.rst.cv.html
    v.surf.rst.cv.md
    v_surf_rst_cv_100_05.png
    v_surf_rst_cv_100_50.png
    v_surf_rst_cv_10_05.png
    v_surf_rst_cv_10_50.png)
