project(r.green.hydro.discharge)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r.green.hydro.discharge_input.png
    r.green.hydro.discharge_output_table.png
    r.green.hydro.discharge_output.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
