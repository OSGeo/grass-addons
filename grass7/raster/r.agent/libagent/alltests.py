#!/usr/bin/env python
############################################################################
#
# MODULE:       r.agent.*
# AUTHOR(S):    michael lustenberger inofix.ch
# PURPOSE:      very basic test collection for the r.agent.* suite
# COPYRIGHT:    (C) 2011 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

import sys

import error
import agent
import ant
import layer
import rasterlayer
import vectorlayer
import world
import aco
import playground

def dotest(function, argv):
    while True:
        n = function.func_doc
        o = str(argv)
        if not n:
            n = str(function)
        t = str(raw_input("execute this now: '"+n+" - "+o+"'? [y/n/abort] "))
        if t == "y":
            if argv != None:
                function(*argv)
            else:
                function()
            break
        elif t == "n":
            break
        elif t == "abort":
            exit()

files = ["elev.grid", "elev.grid.out", "arch.vect"]

alltests = [[error.test, None],
            [agent.test, None],
            [ant.test, None],
            [layer.test, [files[2]]],
            [layer.test, [files[0]]],
            [rasterlayer.test, [files[0]]],
            [vectorlayer.test, [files[2]]],
            [world.test, None],
            [world.test, files],
            [aco.test, files],
            [playground.test, ["raster", files[0], "vector", files[2]]]]

for test in alltests:
    dotest(test[0], test[1])

