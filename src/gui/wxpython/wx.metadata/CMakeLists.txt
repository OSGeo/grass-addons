cmake_minimum_required(VERSION 3.22)

project(wx.metadata)

include(build_addon)

add_subdirectory(config)
add_subdirectory(mdlib)
add_subdirectory(profiles)

set(addons
  db.csw.admin
  db.csw.harvest
  db.csw.run
  g.gui.cswbrowser
  g.gui.metadata
  m.csw.update
  r.info.iso
  t.info.iso
  v.info.iso)

build_addon(
  ${PROJECT_NAME}
  ADDONS ${addons}
  NO_DOCS)
