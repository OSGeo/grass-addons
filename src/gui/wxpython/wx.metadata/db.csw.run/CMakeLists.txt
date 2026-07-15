project(db.csw.run)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES db.csw.run.py
  DOCFILES db.csw.run.html db.csw.run.md)
