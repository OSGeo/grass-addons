project(i.hyper.specresamp)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.hyper.specresamp.py
  DOCFILES
    i.hyper.specresamp.html
    i.hyper.specresamp.md)
