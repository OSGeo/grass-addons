cmake_minimum_required(VERSION 3.22)

project(r.in.vect)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.in.vect.py
  DOCFILES
    r_in_vect_im01.png
    r_in_vect_im02.png
    r_in_vect_im03.png
    r_in_vect_im04.png
    r.in.vect.html
    r.in.vect.md)
