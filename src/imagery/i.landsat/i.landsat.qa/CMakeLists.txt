project(i.landsat.qa)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.landsat.qa.py
  DOCFILES
    i.landsat.qa.html
    i.landsat.qa.md)
