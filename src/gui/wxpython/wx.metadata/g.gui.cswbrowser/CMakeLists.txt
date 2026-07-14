project(g.gui.cswbrowser)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES g.gui.cswbrowser.py
  DOCFILES g.gui.cswbrowser.html g.gui.cswbrowser.md)
