cmake_minimum_required(VERSION 3.22)
project(r.runoff LANGUAGES NONE)

include(build_addon)

set(doc_files
    r.runoff.html
    r.runoff.md
    us_ro_vol.png)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    r.runoff.py
  DOCFILES ${doc_files})
