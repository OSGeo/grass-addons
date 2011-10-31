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

import layer
import error

class VectorLayer(layer.Layer):
    """..."""
    def __init__(self):
        layer.Layer.__init__(self)
        self.objects = []
        self.gissplit = "|"
    def clearlayer(self):
        layer.Layer.clearlayer(self)
        self.objects = []
    def shiftbound(self, direction, delta):
# TODO off by one?
        for obj in self.objects[:]:
            if direction == "north":
                if obj[1] > self.limit[1]+delta:
                    self.objects.remove(obj)
            elif direction == "east":
                if obj[0] > self.limit[0]+delta:
                    self.objects.remove(obj)
            elif direction == "south":
                if obj[1] < self.offset[1]+delta:
                    self.objects.remove(obj)
                else:
                    obj[1] = obj[1]-delta
            elif direction == "west":
                if obj[0] < self.offset[0]+delta:
                    self.objects.remove(obj)
                else:
                    obj[0] = obj[0]-delta
    def reclassify(self, oldres, newres):
# TODO if nothing changes..?
# TODO goes to world??
        dx = (newres[0] + 0.0) / oldres[0]
        dy = (newres[1] + 0.0) / oldres[1]
        for obj in self.objects:
            obj[0] = int(round(obj[0] / dx))
            obj[1] = int(round(obj[1] / dy))
    def forcebounds(self, north, south, east, west, norows=None, nocols=None):
        if self.offset[0] == None or self.offset[0] == self.limit[0]:
            self.setbounds(north, south, east, west)
        else:
            layer.Layer.forcebounds(self, north, south, east, west)
            if norows != None:
                newres = [((east-west)/nocols),((north-south)/norows)]
                self.reclassify(self.resolution, newres)
                self.resolution = newres
    def parsefile(self, fileh):
        self.clearlayer()
        vectorlist = []
        self.offset = [0,0]
        self.limit = [0,0]
        for line in fileh:
            if line[-1] in '\r' '\n' '\r\n':
                line = line[:-1]
            line = line.split(self.gissplit)
            avector = []
            for e in line:
                avector.append(int(e))
            vectorlist.append(avector)
            if avector[0] > int(self.limit[0]):
                self.limit[0] = avector[0]
            if avector[1] > int(self.limit[1]):
                self.limit[1] = avector[1]
        self.objects = vectorlist
    def createfile(self, fileh):
        if self.limit[0] != None:
            for obj in self.objects:
                text = ""
                for element in obj:
                    if text:
                        text = text + self.gissplit + str(element)
                    else:
                        text = str(element)
                fileh.write(text + "\n")

def test(infile, export=True, remove=True):
    """Test suite for VectorLayer Class"""
    outfile = "out-" + infile
    import os
    if os.path.isfile(infile) and not os.path.isfile(outfile):
        print "create vector layer"
        v = VectorLayer()
        v.setinfilename(infile)
        v.setoutfilename(outfile)
        print "importing file"
        v.importfile()
        print "entries # " + str(len(v.objects))
        for o in v.objects:
            print " obj is: x=" + str(o[0]) + " y=" + str(o[1]) + \
                " cat=" + str(o[2])
        print "all between:"
        print " south: " + str(v.offset[1])
        print " west: " + str(v.offset[0])
        print " north: " + str(v.limit[1])
        print " east: " + str(v.limit[0])
        if export == True:
            v.exportfile()
            import filecmp
            if filecmp.cmp(infile, outfile):
                print "import/export seem ok"
            else:
                print "import/export failed"
            if remove == True:
                os.remove(outfile)

        print "creating new example:"
        print " clear all"
        v.clearlayer()
        print " set new values"        
        print "  setting new boundaries: n9, s0, e9, w0"
        v.forcebounds( 9, 0, 9, 0 )
        print "  setting new vectors: 0:5, 5:0, 9:5, 5:9, 5:5"
        v.objects.append([0, 5, 0])
        v.objects.append([5, 0, 1])
        v.objects.append([9, 5, 2])
        v.objects.append([5, 9, 3])
        v.objects.append([5, 5, 4])
        print " set:"
        print "  south: " + str(v.offset[1])
        print "  west: " + str(v.offset[0])
        print "  north: " + str(v.limit[1])
        print "  east: " + str(v.limit[0])
        print " entries # " + str(len(v.objects))
        for o in v.objects:
            print "  obj is: x=" + str(o[0]) + " y=" + str(o[1]) + " cat=" + \
                str(o[2])
        print " set new values"
        print "  setting new boundaries: n6, s4, e6, w4"
        v.forcebounds( 6, 4, 6, 4 )
        print " set:"
        print "  south: " + str(v.offset[1])
        print "  west: " + str(v.offset[0])
        print "  north: " + str(v.limit[1])
        print "  east: " + str(v.limit[0])
        print " remaining entries # " + str(len(v.objects))
        for o in v.objects:             
            print "  obj is: x=" + str(o[0]) + " y=" + str(o[1]) + " cat=" + \
                str(o[2])
        print " again with the old boundaries: n9, s0, e9, w0"
        v.forcebounds( 9, 0, 9, 0 )
        for o in v.objects:
            print "  obj is: x=" + str(o[0]) + " y=" + str(o[1]) + " cat=" + \
                str(o[2])
    else:
        print "Error: no " + infile + " or " + outfile + " exists."

