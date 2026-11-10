cmake_minimum_required(VERSION 3.22)

project(r.scatterplot)

include(build_addon)

set(sources
  main.c
  vector_mask.c
  vector_mask.h)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${sources}
  GRASSLIBS
    gis
    raster
    vector
  DOCFILES
    r_scatterplot_2_variables_3rd_color.png
    r_scatterplot_2_variables_3rd_z_4th_color.png
    r_scatterplot_2_variables_3rd_z_4th_color2.png
    r_scatterplot_2_variables_3rd_z.png
    r_scatterplot_2_variables.png
    r_scatterplot_3_variables_3_colors_overlap.png
    r_scatterplot_3_variables_3_colors.png
    r_scatterplot_3_variables.png
    r_scatterplot_density_full.png
    r_scatterplot_density_grid_hexagons.png
    r_scatterplot_density_grid_rectangles_res_1.png
    r_scatterplot_density_grid_rectangles.png
    r_scatterplot_density_res_120.png
    r_scatterplot_density_res_240.png
    r_scatterplot.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
