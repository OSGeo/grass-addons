cmake_minimum_required(VERSION 3.22)

project(m.cdo.download LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    m_cdo_download_cdo_stations.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
