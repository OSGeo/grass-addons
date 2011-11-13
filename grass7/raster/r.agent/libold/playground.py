############################################################################
#
# MODULE:       r.agent.*
# AUTHOR(S):    michael lustenberger inofix.ch
# PURPOSE:      library file for the r.agent.* suite
# COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

import rasterlayer
import vectorlayer

class Playground(object):
    """..."""
    def __init__(self):
        self.layers = dict()
        self.offset = [None,None]
        self.limit = [None,None]
        self.steps = []
    def setbounds(self, north=None, south=None, east=None, west=None,
                     rows=None, cols=None):
        self.offset = [west,south]
        self.limit = [east,north]
        # here always try to set steps (see Layer)
        if rows:
            self.steps = [cols,rows]
    def setboundsfromlayer(self, layername):
        self.setbounds(*self.layers[layername].getbounds())
    def getbounds(self):
        if self.steps:
            rows = self.steps[1]
            cols = self.steps[0]
        else:
            rows = None
            cols = None
        return [self.limit[1], self.offset[1], self.limit[0],
                self.offset[0], rows, cols]
    def getrelativebounds(self):
        b = self.getbounds()
        b = [b[4]-1,0,b[5]-1,0,b[4],b[5]]
        return b
    def setlayeralias(self, layername, layer):
        self.layers[layername] = layer
    def removelayer(self, layername):
        del self.layers[layername]
    def getlayer(self, layername):
        return self.layers[layername]
    def setlayer(self, layername, layer, force=False):
        self.layers[layername] = layer
        if force and self.offset[0] != None:
            self.layers[layername].forcebounds(*self.getbounds())
    def setnewlayer(self, layername, typename, force=False):
        if typename == "raster":
            layer = rasterlayer.RasterLayer()
        elif typename == "vector":
            layer = vectorlayer.VectorLayer()
#        elif typename == "graph":
#            self.layers[layername] = layer.Layer()
        else:
            print "layertype not supported (yet)."
        self.setlayer(layername, layer, force)
    def setlayerfromfile(self, layername, typename, filename):
        self.setnewlayer(layername, typename)
        self.layers[layername].setinfilename(filename)
        self.layers[layername].importfile()
        if self.offset[0] != None:
            self.layers[layername].forcebounds(*self.getbounds())
    def forcelayerbounds(self):
        if self.offset[0] != None:
            for layer in self.layers.itervalues():
                layer.forcebounds(*self.getbounds())

def test(layer0type=None, layer0=None, layer1type=None, layer1=None):
    """Test suite for Playground Class"""
    def testhelper(north=None, south=None, east=None, west=None,
                     rows=None, cols=None):
        print " It has this boundaries: "
        print "  south: " + str(south)
        print "  west: " + str(west)
        print "  north: " + str(north)
        print "  east: " + str(east)
        print "  rows: " + str(rows)
        print "  cols: " + str(cols)
    print "creating new Playground.."
    pg = Playground()
    print "start filling it up.."
    if layer0:
        pg.setlayerfromfile("l0", layer0type, layer0)
    else:
        pg.setbounds(20, 0, 20, 0, 20, 20)
        pg.setnewlayer("l0", "raster", True)
        layer0type="raster"
    print "Layer: "+"l0"+" ("+layer0type+")"
    testhelper(*pg.layers["l0"].getbounds())
    if layer1:
        pg.setlayerfromfile("l1", layer1type, layer1)
    else:
        pg.setnewlayer("l1", "vector", True)
        layer1type="vector"
    print "Layer: "+"l1"+" ("+layer1type+")"
    testhelper(*pg.layers["l1"].getbounds())
    print "Setting global boundaries from layer l0"
    pg.setboundsfromlayer("l0")
    testhelper(*pg.getbounds())
    print "adding new name/alias for l0"
    pg.setlayeralias("newname", pg.getlayer("l0"))
    print " " + str(pg.layers.keys())
    testhelper(*pg.layers["newname"].getbounds())
    print "remove new name"
    pg.removelayer("newname")
    print str(pg.layers.keys())
    print "force global boundaries on layers"
    pg.forcelayerbounds()
    print " l1"
    testhelper(*pg.layers["l1"].getbounds())

