project(r.green.biomassfor.theoretical)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    theoretical_input.png
    theoretical_output.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
