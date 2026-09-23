project(i.sentinel.download)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    i.sentinel.download.py
  DOCFILES
    i.sentinel.download.html
    i.sentinel.download.md)
