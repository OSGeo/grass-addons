project(r.info.iso)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.info.iso.py
  DOCFILES r.info.iso.html r.info.iso.md)
