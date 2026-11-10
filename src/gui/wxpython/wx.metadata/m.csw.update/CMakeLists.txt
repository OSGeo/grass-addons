project(m.csw.update)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES m.csw.update.py
  DOCFILES m.csw.update.html m.csw.update.md)
