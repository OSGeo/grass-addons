project(i.sentinel.import)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES
    i.sentinel.import.py
  DOCFILES
    i_sentinel_import_with_cloud_shadow_mask_v1.png
    i_sentinel_import_with_cloud_shadow_mask_v2.png
    i_sentinel_import_without_cloud_mask.png
    i.sentinel.import.html
    i.sentinel.import.md)
