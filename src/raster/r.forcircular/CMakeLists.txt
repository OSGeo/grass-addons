cmake_minimum_required(VERSION 3.22)

project(r.forcircular LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    avoided_emission.png
    dip.png
    parcel.png
    stumpage_function.png
    stumpage.png
    tech_function.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
