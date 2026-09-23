project(i.hyper.composite)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.hyper.composite.py
  DOCFILES
    i.hyper.composite.html
    i.hyper.composite.md)
