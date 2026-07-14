project(db.csw.harvest)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES db.csw.harvest.py
  DOCFILES db.csw.harvest.html db.csw.harvest.md)
