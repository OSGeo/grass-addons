project(r.green.hydro.planning)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_hydro_planning_input_PNAM.png
    r_green_hydro_planning_input.png
    r_green_hydro_planning_output_park.png
    r_green_hydro_planning_output_PNAM3.png
    r_green_hydro_planning_output_points.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
