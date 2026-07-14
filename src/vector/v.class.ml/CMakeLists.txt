cmake_minimum_required(VERSION 3.22)

project(v.class.ml)

include(build_addon)

add_files_to_etc_dir(
  ${PROJECT_NAME}
  FILES
    features.py
    ml_classifiers.py
    ml_functions.py
    npy2table.py
    sqlite2npy.py
    training_extraction.py)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.class.ml.py
  DOCFILES
    v.class.ml.html
    v.class.ml.md)
