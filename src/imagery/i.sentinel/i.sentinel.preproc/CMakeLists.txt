project(i.sentinel.preproc)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    i.sentinel.preproc.py
  DOCFILES
    i_sentinel_preproc_ES.png
    i_sentinel_preproc_GWF.png
    i.sentinel.preproc.html
    i.sentinel.preproc.md)
