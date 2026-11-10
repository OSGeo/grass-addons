cmake_minimum_required(VERSION 3.22)

project(v.civil)

include(build_addon)

add_files_to_etc_dir(
  ${PROJECT_NAME}
  FILES
    road_base.py
    road_crosstools.py
    road_displ.py
    road_marks.py
    road_plant.py
    road_profiles.py
    road_road.py
    road_tables.py
    road_terr.py
    road_topotools.py
    road_trans.py
    road_vertical.py)

set(doc_files
  img_a_plan.png
  img_a_tooladdrow.png
  img_a_topotools_1.png
  img_a_vcivilroad_7.png
  img_a_vert.png
  img_tables1.png
  img_tables2_2.png
  img_tables2_3.png
  img_tables2.png
  img_tables3_1.png
  img_tables3_2.png
  img_tables3.png
  img_tables4_1.png
  img_tables4_2.png
  img_tables5_1.png
  img_tables6_1.png
  img_tables7_1.png
  img1.png
  img2_1.png
  img2.png
  img3_2.png
  img3.png
  img4_1.png
  img4_2.png
  img4_3.png
  img4.png
  img5.png
  img6_1.png
  img6.png
  img7.png
  img8_1.png
  img8_2.png
  v.civil.html
  v.civil.md)

build_addon(
  ${PROJECT_NAME}
  SOURCES v.civil.py
  DOCFILES ${doc_files})
