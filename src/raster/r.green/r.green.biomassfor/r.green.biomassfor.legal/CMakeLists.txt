project(r.green.biomassfor.legal)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    legal_input.png
    legal_output.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
