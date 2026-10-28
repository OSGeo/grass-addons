project(i.sentinel.coverage)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    i.sentinel.coverage.py
  DOCFILES
    i.sentinel.coverage.html
    i.sentinel.coverage.md)
