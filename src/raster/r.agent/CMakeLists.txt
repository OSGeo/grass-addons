cmake_minimum_required(VERSION 3.22)

project(r.agent LANGUAGES NONE)

include(build_addon)

add_subdirectory(libagent)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.agent.aco
    r.agent.rand
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
