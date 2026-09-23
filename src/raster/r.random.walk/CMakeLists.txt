cmake_minimum_required(VERSION 3.22)

project(r.random.walk LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_random_walk_example_2.png
    r_random_walk_example.png
    random_walk_output.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
