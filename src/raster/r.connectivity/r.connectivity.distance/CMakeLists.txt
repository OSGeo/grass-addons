project(r.connectivity.distance)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_connectivity_distance_costs.png
    r_connectivity_distance_network.png
    r_connectivity_distance_patches.png
    r_connectivity_distance_shortest_paths.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
