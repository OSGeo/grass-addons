project(i.hyper.preproc)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.hyper.preproc.py
  DOCFILES
    i.hyper.preproc.html
    i.hyper.preproc.md)
