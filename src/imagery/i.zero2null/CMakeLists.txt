cmake_minimum_required(VERSION 3.22)

project(i.zero2null LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i_zero2null_s2_corr.png
    i_zero2null_s2_uncorr.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
