project(i.landsat.import)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.landsat.import.py
  DOCFILES
    i.landsat.import.html
    i.landsat.import.md)
