project(r.green.hydro.technical)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_hydro_technical_input.png
    r_green_hydro_technical_output.png
    r_green_hydro_technical_picstruct.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
