project(r.green.biomassfor)

include(build_addon)

add_subdirectory(libforest)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.green.biomassfor.co2
    r.green.biomassfor.financial
    r.green.biomassfor.impact
    r.green.biomassfor.legal
    r.green.biomassfor.recommended
    r.green.biomassfor.technical
    r.green.biomassfor.theoretical
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
