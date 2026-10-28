project(i.hyper.import)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES i.hyper.import.py
  DOCFILES
    i.hyper.import.html
    i.hyper.import.md
    import_example.jpg
    import_example2.jpg
    import_example3.jpg)
