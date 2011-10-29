############################################################################
#
# MODULE:       r.agent.*
# AUTHOR(S):    michael lustenberger inofix.ch
# PURPOSE:      library file for the r.agent.* suite
# COPYRIGHT:    (C) 2011 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

import error

class Layer():
    """More like a meta/stub Class (or Interface).
        To be inherited by children."""
    def __init__(self):
        self.infilename = None
        self.outfilename = None
        self.offset = [None,None]
        self.limit = [None,None]
        self.steps = []
        self.resolution = [1,1]
        self.fbuffer = None
    def setinfilename(self, filename):
        self.infilename = filename
    def setoutfilename(self, filename):
        self.outfilename = filename
    def clearlayer(self):
        self.offset = [None, None]
        self.limit = [None, None]
        if self.steps != []:
            self.steps = [None, None]
    def setbounds(self, north, south, east, west, rows=None, cols=None):
        self.offset = [west,south]
        self.limit = [east,north]
        # here layer decides if steps shall be set (see Playground)
        if self.steps != []:
            self.steps = [cols,rows]
            self.resolution[0] = (self.limit[0]-self.offset[0])/self.steps[0]
            self.resolution[1] = (self.limit[1]-self.offset[1])/self.steps[1]
    def getbounds(self):
        if self.steps != []:
            rows = self.steps[1]
            cols = self.steps[0]
        else:
            rows = None
            cols = None
        return [self.limit[1], self.offset[1], self.limit[0],
                 self.offset[0], rows, cols]
    def shiftbound(self, direction, delta):
        if delta < 0:
            pass
        elif delta > 0:
            pass
    def comparebounds(self, north, south, east, west, rows=None, cols=None):
        if [west,south] == self.offset and [east,north] == self.limit:
            if self.steps == []:
                return True
            elif [cols,rows] == self.steps:
                return True
        return False
    def forcebounds(self, north, south, east, west, rows=None, cols=None):
        if not self.comparebounds(north, south, east, west, rows, cols):
            if self.resolution[0] and self.resolution[1]:
                xres = self.resolution[0]
                yres = self.resolution[1]
            else:
                xres = 1
                yres = 1
            self.shiftbound('north', (north-self.limit[1])/yres)
            self.shiftbound('south', (south-self.offset[1])/yres)
            self.shiftbound('east', (east-self.limit[0])/xres)
            self.shiftbound('west', (west-self.offset[0])/xres)
            self.setbounds(north, south, east, west, rows, cols)
    def parsefile(self, fileh):
        self.fbuffer = fileh.read()
    def createfile(self, fileh):
        if self.fbuffer:
            fileh.write(self.fbuffer)
    def importfile(self):
        try:
            with open(self.infilename, 'r') as fileh:
                self.parsefile(fileh)
        except IOError:
            print "Error: Can not read " + self.infilename
        except error.InputError:
            print "Error: " + self.infilename + \
                    " is not a valid ascii file"
    def exportfile(self):
        try:
            with open(self.outfilename, "w") as fileh:
                self.createfile(fileh)
        except IOError:
            print "Error: Can not write", self.infilename

def test(infile, export=True, remove=True):
    """Test suite for Layer Class"""
    outfile = "out-" + infile
    import os
    if os.path.isfile(infile) and not os.path.isfile(outfile):
        l = Layer()
        print "setting files.."
        l.setinfilename(infile)
        l.setoutfilename(outfile)
        print " import"
        l.importfile()
        if export == True:
            print " export"
            l.exportfile()
            import filecmp
            if filecmp.cmp(infile, outfile):
                print "import/export seem ok"
            else:
                print "import/export failed"
            if remove == True:
                os.remove(outfile)
        print "setting bounds"
        l.setbounds(9,0,10,1)
        print " bounds:", str(l.getbounds())
        print " offset/limit:", str(l.offset), str(l.limit)
        print "comparing bounds: "
        print " True:",str(l.comparebounds(*l.getbounds()))
        print " False:",str(l.comparebounds(l.offset[0]+1,l.offset[1],*l.limit))
        print "clear all"
        print "all again with steps:"
        l.setbounds(9,0,10,1,1,1)
        print " bounds:", str(l.getbounds())
        print " offset/limit:", str(l.offset), str(l.limit)
        print "comparing bounds: "
        print " True:",str(l.comparebounds(*l.getbounds()))
        print " False:",str(l.comparebounds(l.offset[0]+1,l.offset[1],*l.limit))
        print "clear all"
        l.clearlayer()
        print " noting: "+str(l.offset)+str(l.limit)
    else:
        print "Error: no " + infile + " or " + outfile + " exists."

