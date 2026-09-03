cmake_minimum_required(VERSION 3.22)
project(r.soils.rosetta)

include(build_addon)

build_addon(
    ${PROJECT_NAME}
    SOURCES
        r.soils.rosetta.py
    DOCFILES
        r.soils.rosetta.html
        r.soils.rosetta.md)
