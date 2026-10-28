project(i.hyper.explore)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.hyper.explore.py
  DOCFILES
    explore_example1.jpg
    explore_example2.jpg
    i.hyper.explore.html
    i.hyper.explore.md)
