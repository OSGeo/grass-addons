project(r.green.hydro.structure)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_hydro_structure_input.png
    r_green_hydro_structure_output.png
    r_green_hydro_structure_picstruct.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
