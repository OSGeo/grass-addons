project(i.hyper.export)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.hyper.export.py
  DOCFILES
    i.hyper.export.html
    i.hyper.export.md)
