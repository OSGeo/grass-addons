project(r.futures.devpressure LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    devpressure_example.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
