project(r.green.hydro)

include(build_addon)

add_subdirectory(libhydro)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.green.hydro.closest
    r.green.hydro.delplants
    r.green.hydro.discharge
    r.green.hydro.financial
    r.green.hydro.optimal
    r.green.hydro.planning
    r.green.hydro.recommended
    r.green.hydro.structure
    r.green.hydro.technical
    r.green.hydro.theoretical
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
