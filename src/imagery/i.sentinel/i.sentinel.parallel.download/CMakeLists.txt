project(i.sentinel.parallel.download)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    i.sentinel.parallel.download.py
  DOCFILES
    i.sentinel.parallel.download.html
    i.sentinel.parallel.download.md)
