cmake_minimum_required(VERSION 3.22)

project(r.hand)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.hand.py
  DOCFILES
    r.hand.html
    r.hand.md
    r_hand.png
    r_hand_class.png
    r_hand_color.png)
