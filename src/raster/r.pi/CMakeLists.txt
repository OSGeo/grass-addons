cmake_minimum_required(VERSION 3.22)

project(r.pi)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  ADDONS
    r.pi.corearea
    r.pi.corr.mw
    r.pi.csr.mw
    r.pi.energy
    r.pi.energy.pr
    r.pi.enn
    r.pi.enn.pr
    r.pi.export
    r.pi.fnn
    r.pi.graph
    r.pi.graph.dec
    r.pi.graph.pr
    r.pi.graph.red
    r.pi.grow
    r.pi.import
    r.pi.index
    r.pi.library
    r.pi.lm
    r.pi.neigh
    r.pi.nlm
    r.pi.nlm.circ
    r.pi.nlm.stats
    r.pi.odc
    r.pi.prob.mw
    r.pi.prox
    r.pi.rectangle
    r.pi.searchtime
    r.pi.searchtime.mw
    r.pi.searchtime.pr
  DOCFILES
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
