project(i.sentinel.mask)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    i.sentinel.mask.py
  DOCFILES
    i_sentinel_mask_CD.png
    i_sentinel_mask_CS.png
    i_sentinel_mask_ES.png
    i_sentinel_mask_GWF.png
    i_sentinel_mask_indonesia_esa_sen2cor.png
    i_sentinel_mask_indonesia_grass_gis.png
    i_sentinel_mask_SD.png
    i.sentinel.mask.html
    i.sentinel.mask.md)
