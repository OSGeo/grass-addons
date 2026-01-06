project(g.gui.metadata)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES g.gui.metadata.py
  DOCFILES g.gui.metadata.html g.gui.metadata.md)
