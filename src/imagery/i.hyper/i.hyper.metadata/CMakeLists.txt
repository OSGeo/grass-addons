project(i.hyper.metadata)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.hyper.metadata.py
  DOCFILES
    i.hyper.metadata.html
    i.hyper.metadata.md)
