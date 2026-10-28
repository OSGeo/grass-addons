cmake_minimum_required(VERSION 3.22)

project(v.stream.order)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    stream_network_order_drwal.png
    stream_network_order_scheidegger.png
    stream_network_order_shreve.png
    stream_network_order_strahler.png
    stream_network.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
