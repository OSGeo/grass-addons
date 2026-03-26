project(r.green.hydro.recommended)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_hydro_recommended_input_PNAM.png
    r_green_hydro_recommended_input.png
    r_green_hydro_recommended_output_park.png
    r_green_hydro_recommended_output_PNAM3.png
    r_green_hydro_recommended_output_points.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
