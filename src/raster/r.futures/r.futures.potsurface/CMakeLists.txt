project(r.futures.potsurface LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_futures_potsurface.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
