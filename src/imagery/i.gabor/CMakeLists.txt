cmake_minimum_required(VERSION 3.22)

project(i.gabor LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i_gabor_imaginary.png
    i_gabor_individual.png
    i_gabor_ortho.png
    i_gabor_quant.png
    i_gabor_segment.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
