cmake_minimum_required(VERSION 3.22)
project(r.in.ssurgo)

include(build_addon)

build_addon(
    ${PROJECT_NAME}
    SOURCES
        r.in.ssurgo.py
    DOCFILES
        r.in.ssurgo.html
        r.in.ssurgo.md)
