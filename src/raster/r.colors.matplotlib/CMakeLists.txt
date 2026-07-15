cmake_minimum_required(VERSION 3.22)

project(r.colors.matplotlib)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES r.colors.matplotlib.py
  DOCFILES
    r.colors.matplotlib.html
    r.colors.matplotlib.md
    r_colors_matplotlib.png
    r_colors_matplotlib_autumn.png
    r_colors_matplotlib_cubehelix_discrete.png
    r_colors_matplotlib_gist_earth.png
    r_colors_matplotlib_gist_earth_discrete.png
    r_colors_matplotlib_terrain.png
    r_colors_matplotlib_viscm.png
    r_colors_matplotlib_viscm_edit.png
    r_colors_matplotlib_viscm_properties.png
    r_colors_matplotlib_winter_discrete.png)
