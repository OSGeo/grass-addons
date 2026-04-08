cmake_minimum_required(VERSION 3.22)

project(i.fusion.hpf LANGUAGES NONE)

include(build_addon)

add_files_to_etc_dir(
  ${PROJECT_NAME}
  FILES
    constants.py
    high_pass_filter.py)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    i_fusion_hpf_lsat7_hpf_rgb.png
    i_fusion_hpf_lsat7_orig_rgb.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
