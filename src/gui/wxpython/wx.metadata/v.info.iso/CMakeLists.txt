project(v.info.iso)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.info.iso.py
  DOCFILES v.info.iso.html v.info.iso.md)
