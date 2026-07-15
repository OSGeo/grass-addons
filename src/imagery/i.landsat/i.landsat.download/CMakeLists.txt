project(i.landsat.download)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.landsat.download.py
  DOCFILES
    i.landsat.download.html
    i.landsat.download.md)
