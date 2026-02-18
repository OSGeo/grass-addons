cmake_minimum_required(VERSION 3.22)
project(r.in.ssurgo)

include(build_addon)

# ## Ensure libsoil is configured so its targets (libsoil, install_addon) are available
# if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/../libsoil/CMakeLists.txt")
#   add_subdirectory("${CMAKE_CURRENT_LIST_DIR}/../libsoil" EXCLUDE_FROM_ALL)
# endif()

build_addon(
    ${PROJECT_NAME}
    SOURCES
        r.in.ssurgo.py
    DOCFILES
        r.in.ssurgo.html
        r.in.ssurgo.md)

# Make sure building this addon will run the libsoil install helper so the
# GRASS addons directory gets the up-to-date soillib files.
# add_dependencies(${PROJECT_NAME} libsoil)
