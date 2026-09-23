project(r.connectivity.corridors)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_connectivity_corridors_cf_u_sum_all.png
    r_connectivity_corridors_mst_eb.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
