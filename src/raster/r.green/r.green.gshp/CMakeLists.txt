project(r.green.gshp)

include(build_addon)

add_subdirectory(libgshp)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.green.gshp.technical
    r.green.gshp.theoretical
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
