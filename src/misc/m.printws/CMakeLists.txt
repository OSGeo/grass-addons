cmake_minimum_required(VERSION 3.22)

project(m.printws LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    m.printws_filledagainwindow.png
    m.printws_fullwindow.png
    m.printws_pan.png
    m.printws_sample_print.png
    m.printws_screen.png
    m.printws_smallerwindow.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
