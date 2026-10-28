project(r.green.install)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_install_permissions.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
