project(r.green.hydro.financial)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_green_hydro_financial_compmap.png
    r_green_hydro_financial_excmap.png
    r_green_hydro_financial_fcompensation.png
    r_green_hydro_financial_fexcavation.png
    r_green_hydro_financial_fgamma.png
    r_green_hydro_financial_flinearcost.png
    r_green_hydro_financial_fnpv.png
    r_green_hydro_financial_fvu.png
    r_green_hydro_financial_input.png
    r_green_hydro_financial_tableeco.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
