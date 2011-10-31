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

class RasterLayer(layer.Layer):
    """..."""
    def __init__(self):
        layer.Layer.__init__(self)
        self.bkeys = ["north", "south", "east", "west", "rows", "cols"]
        self.steps = [None,None]
        self.resolution = [None,None]
        self.raster = []
        self.gisempty = "*"
        self.emptyvalue = -1
    def clearlayer(self):
        layer.Layer.clearlayer(self)
        self.raster = []
    def xyflipmatrix(self, matrix):
        newmatrix = []
        for i in range(len(matrix[0])):
            newrow = []
            for j in range(len(matrix)):
                newrow.append(matrix[j][i])
            newmatrix.append(newrow)
        return newmatrix
    def xflipmatrix(self, matrix):
        raster = []
        for i in range(len(matrix)-1, -1, -1):
            raster.append(matrix[i])
        return raster
    def shiftbound(self, direction, delta):
        if delta < 0:
            if direction == "east":
                for i in range(delta, 0):
                    del self.raster[-1]
            elif direction == "west":
                for i in range(delta, 0):
                    self.raster.insert(0,
                        [0 for i in range(len(self.raster[0]))])
            elif direction == "north":
                for i in range(delta, 0):
                    for j in range(len(self.raster)):
                        del self.raster[j][-1]
            elif direction == "south":
                for i in range(delta, 0):
                    for j in range(len(self.raster)):
                        self.raster[j].insert(0, 0)
        if delta > 0:
            if direction == "east":
                for i in range(delta):
                    self.raster.append([0 for i in range(len(self.raster[0]))])
            elif direction == "west":
                for i in range(delta):
                    del self.raster[0]
            elif direction == "north":
                for i in range(delta):
                    for j in range(len(self.raster)):
                        self.raster[j].append(0)
            elif direction == "south":
                for i in range(delta):
                    for j in range(len(self.raster)):
                        del self.raster[j][0]
    def testresolution(self, north, south, east, west, rows, cols):
        if rows > 0 < cols:
            xres = ( east - west ) / cols
            yres = ( north - south ) / rows
            if self.resolution[0] == xres and self.resolution[1] == yres:
                return True
        return False
    def forcebounds(self, north, south, east, west, rows, cols):
        if self.steps[0] == None and self.raster == []:
            self.setbounds(north, south, east, west, rows, cols)
            for i in range(cols):
                self.raster.append([0 for j in range(rows)])
        elif not self.testresolution(north, south, east, west, rows, cols):
            raise error.DataError("raster.forcebounds", "wrong resolution")
        else:
            layer.Layer.forcebounds(self, north, south, east, west, rows, cols)
    def parsefile(self, fileh):
        self.clearlayer()
        bounds = []
        for key in self.bkeys:
            keylength = len(key)
            line = fileh.readline()
            if line[0:keylength] in key:
                bounds.append(int(line[keylength+2:-1]))
            else:
                raise error.InputError(self.infilename, "no valid raster")
        self.setbounds(*bounds)
        raster = []
        for line in fileh:
            rasterline = []
            for word in line.split(" "):
                if word.find(".") > 0:
                    rasterline.append(float(word))
                elif word.isdigit():
                    rasterline.append(int(word))
                elif word in '\r' '\n' '\r\n':
                    pass
                else:
                    rasterline.append(self.emptyvalue)
            raster.append(rasterline[:])
        if not (len(raster) == self.steps[1] and
                        len(raster[0]) == self.steps[0]):
            raise error.InputError(self.infilename, "wrong # rows/cols")
        self.raster = self.xyflipmatrix(self.xflipmatrix(raster))
    def createfile(self, fileh):
        if self.limit[0]:
            raster = self.xflipmatrix(self.xyflipmatrix(self.raster))
            bounds = self.getbounds()
            bounds.reverse()
            for key in self.bkeys:
                line = key + ": " + str(bounds.pop()) + "\n"
                fileh.writelines(line)
            for line in raster:
                for word in line:
                    if word == self.emptyvalue:
                        fileh.write(self.gisempty + " ")
                    else:
                        fileh.write(str(word) + " ")
                fileh.write("\n")

def test(infile, export=True, remove=True):
    """Test suite for RasterLayer Class"""
    outfile = "out-" + infile
    import os
    if os.path.isfile(infile) and not os.path.isfile(outfile):
        print "create raster layer"
        r = RasterLayer()
        r.setinfilename(infile)
        r.setoutfilename(outfile)
        print "importing file.."
        r.importfile()
        print "file says:"
        print " r:", str(r.steps[0])+"; c:", str(r.steps[1])
        print "matrix:"
        print " x:", str(len(r.raster))+"; y:", str(len(r.raster[0]))
        if export == True:
            r.exportfile()
            import filecmp
            if filecmp.cmp(infile, outfile):
                print "import/export seem ok"
            else:
                print "import/export failed"
            if remove == True:
                os.remove(outfile)
        print "properties are still:"
        print " r:", str(r.steps[0])+"; c:", str(r.steps[1])
        print "flipping raster on x:"
        b = r.xflipmatrix(r.raster)               
        print " x:", str(len(b))+"; y:", str(len(b[0]))
        print "flipping raster on x/y:"
        b = r.xyflipmatrix(r.raster)
        print " x:", str(len(b))+"; y:", str(len(b[0]))
        print "a little resolution test first (to be True):", \
                str(r.testresolution(*r.getbounds()))
        print "now force bounds on raster: "
        print " the same as now"
        r.forcebounds(*r.getbounds())
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                    str(r.steps)
        print "  at position [0,0] we have now:", str(r.raster[0][0])
        print " setting new values now: 100,0,100,0,1,1"
        r.clearlayer()
        r.forcebounds(100,0,100,0,1,1)
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                    str(r.steps)
        print "  testing wheter they are set now (True):", \
                str(r.testresolution(100,0,100,0,1,1))
        print "  at position [0,0] we have now: ", str(r.raster[0][0])
        print " momentary raster:"
        print str(r.raster)
        print " now reforcing these (correct) values: 200,100,200,100,1,1"
        r.forcebounds(200,100,200,100,1,1)
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                    str(r.steps)
        print " momentary raster:"
        print str(r.raster)
        print " now some wrong values, should throw Error.."
        try:
            r.forcebounds(0,0,1,1,1,10000)
        except error.DataError:
            print "expected Error received.."
        print " momentary raster:"
        print str(r.raster)
        print " changeing value r[0][0] to 1"
        r.raster[0][0] = 1
        print " momentary raster:"
        print str(r.raster)
        print "adding some space in the north"
        print " setting new values now: 400,100,200,100,3,1"
        r.forcebounds(400,100,200,100,3,1)
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print " momentary raster:"
        print str(r.raster)
        print "removing some space in the north"
        print " setting new values now: 300,100,200,100,2,1"
        r.forcebounds(300,100,200,100,2,1)
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print " momentary raster:"
        print str(r.raster)
        print "adding some space in the east"
        r.forcebounds(300,100,400,100,2,3)
        print " momentary raster:"
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print str(r.raster)
        print "removing some space in the east"
        r.forcebounds(300,100,300,100,2,2)
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print " momentary raster:"
        print str(r.raster)
        print "adding some space in the south"
        r.forcebounds(300,0,300,100,3,2)
        print " momentary raster:"
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print str(r.raster)
        print "removing some space in the south"
        r.forcebounds(300,100,300,100,2,2)
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print " momentary raster:"
        print str(r.raster)
        print "adding some space in the west"
        r.forcebounds(300,100,300,0,2,3)
        print " momentary raster:"
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print str(r.raster)
        print "removing some space in the west"
        r.forcebounds(300,100,300,100,2,2)
        print "  n/w:", str(r.offset), "s/e:", str(r.limit), "r/c:", \
                str(r.steps), "::", str(len(r.raster[0]))+":"+str(len(r.raster))
        print " momentary raster:"
        print str(r.raster)
    else:
        print "Failed: no", infile, "or", outfile, "exists."

