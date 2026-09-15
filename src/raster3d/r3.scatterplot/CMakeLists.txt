cmake_minimum_required(VERSION 3.22)

project(r3.scatterplot)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  GRASSLIBS
    gis
    raster3d
    vector
  SOURCES
    main.c
    vector_mask.c
    vector_mask.h
  DOCFILES
    r3_scatterplot_2_variables_3rd_color.png
    r3_scatterplot_2_variables_3rd_z_4th_color.png
    r3_scatterplot_2_variables_3rd_z_4th_color2.png
    r3_scatterplot_2_variables_3rd_z.png
    r3_scatterplot_2_variables.png
    r3_scatterplot_2d.png
    r3_scatterplot_3_variables_3_colors_overlap.png
    r3_scatterplot_3_variables_3_colors.png
    r3_scatterplot_3_variables.png
    r3_scatterplot.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
