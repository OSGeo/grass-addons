project(r.connectivity.network)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
  overview.png
    r_connectivity_network_deg_udc.png
    r_connectivity_network_ebc_udc.png
    r_connectivity_network_kernel.png
    r_connectivity_network_overview.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
