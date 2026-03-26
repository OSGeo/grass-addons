cmake_minimum_required(VERSION 3.22)

project(r.mess LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_mess_Ex_01.png
    r_mess_Ex_02.png
    r_mess_Ex_03.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
