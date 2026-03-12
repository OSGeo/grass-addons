project(r.green.hydro.optimal)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_hydro_optimal_input.png
    r_green_hydro_optimal_output.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
