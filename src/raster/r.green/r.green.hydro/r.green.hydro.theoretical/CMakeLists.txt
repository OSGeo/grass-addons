project(r.green.hydro.theoretical)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_hydro_theoretical_input.png
    r_green_hydro_theoretical_output.png
    r_green_hydro_theoretical_streams.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
