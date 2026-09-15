project(t.info.iso)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES t.info.iso.py
  DOCFILES t.info.iso.html t.info.iso.md)
