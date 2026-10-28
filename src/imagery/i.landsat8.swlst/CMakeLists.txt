cmake_minimum_required(VERSION 3.22)

project(i.landsat8.swlst)

include(build_addon)

add_files_to_etc_dir(
  ${PROJECT_NAME}
  FILES
    column_water_vapor.py
    constants.py
    csv_to_dictionary.py
    data_validation.py
    dummy_mapcalc_strings.py
    emissivity.py
    helpers.py
    landsat8_mtl.py
    radiance.py
    randomness.py
    split_window_lst.py
    temperature.py)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.landsat8.swlst.py
  DOCFILES
    i.landsat8.swlst.html
    i.landsat8.swlst.md)
