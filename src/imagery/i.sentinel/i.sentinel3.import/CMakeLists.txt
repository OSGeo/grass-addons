project(i.sentinel3.import)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    i.sentinel3.import.py
  DOCFILES
    i.sentinel3.import.html)
