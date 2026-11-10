project(db.csw.admin)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES db.csw.admin.py
  DOCFILES db.csw.admin.html db.csw.admin.md)
