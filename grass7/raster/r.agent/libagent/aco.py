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

from math import sqrt
from math import exp
from random import randint
import world
import error
import ant

class ACO(world.World):
    """Ant Colony Optimization Algorithm for Modelling an Agent Based World"""
    def __init__(self):
        world.World.__init__(self, ant.Ant)
        ### auto/constant
        self.agentclass = ant.Ant
        self.ants = self.agents
        self.artefacts.append([])
        self.holes = self.artefacts[0]
        self.artefacts.append([])
        self.sugar = self.artefacts[1]
        self.surfaceslope = None
        self.costsurface = None
        self.pherovapour = None
        self.bounds = None
        self.straight = 0
        self.diagonal = sqrt(2)-1
        # count paths
        self.nrop = 0
        ### user parameter
        self.globalfreedom = 8
        self.rounds = 0
        self.outrounds = 0
        self.outfilename = ""
        self.maxpheromone = 2147483647
        self.minpheromone = 10
        self.volatilizationtime = 1
        self.stepintensity = 10
        self.pathintensity = 10000
        self.decisionbase = "standard"
        self.pheroweight = 1
        self.randomweight = 1
        self.validposition = "specials"
# use fibonacci?
        self.maxants = 100
        self.antslife = 0
    def checkvalues(self):
        if self.costsurface == None:
            raise error.DataError("aco.ACO.checkvalues()",
                    "main input missing: costraster")
        self.playground.setboundsfromlayer("costs")
        self.playground.forcelayerbounds()
        self.bounds = self.playground.getrelativebounds()
        if self.costsurface == None:
            raise error.DataError("aco.ACO.checkvalues()",
                    "input layer missing: costsurface")
        elif self.costsurface == []:
            if self.surfaceslope == None:
                raise error.DataError("aco.ACO.checkvalues()",
                    "input layer missing: please provide cost or slope layer")
            else:
                self.calccostsurface()
        if self.pherovapour == None:
            raise error.DataError("aco.ACO.checkvalues()",
                    "output layer missing: pheromoneraster")
        if self.holes == None:
            raise error.DataError("aco.ACO.checkvalues()",
                    "input layer missing: vectorholes")
        if self.rounds <= 0:
            raise error.DataError("aco.ACO.checkvalues()",
                    "number of rounds is zero or not set.")
        if self.outrounds <= 0:
            self.outrounds = self.rounds
        if self.antslife == 0:
            self.antslife = (self.bounds[4]+self.bounds[5])
        if self.volatilizationtime > self.rounds:
            self.volatilizationtime = self.rounds
        elif self.volatilizationtime < 0:
            self.volatilizationtime = 0
        for hole in self.holes[:]:
            if self.costsurface[hole[0]][hole[1]] < 0:
                self.holes.remove(hole)
            else:
# TODO if two holes are close, choose outermost.. or so.
                self.pherovapour[hole[0]][hole[1]] = -1
    def addneighbour(self, positions, position):
        position[2] = self.costsurface[position[0]][position[1]]
# TODO > or >=
        if position[2] >= 0:
            position[3] = self.pherovapour[position[0]][position[1]]
            positions.append(position)
    def calccostsurface(self):
        for x in range(self.bounds[2]):
            for y in range(self.bounds[0]):
                val = self.surfaceslope[x][y]
                if self.surfaceslope > 0:
                    self.costsurface[x][y] = (1/exp(-0.035*abs(val+5)))-1
    def getneighbourpositions(self, position, freedom=None):
        # position = [ x, y, surfacecost, special/phero, timecost, direction ]
        if freedom == None:
            freedom = self.globalfreedom
        positions = []
        if freedom >= 4:
            #north = 1
#TODO improve with not creating position in any case..
            p = [position[0], position[1]+1, 0, 0, self.straight, 1]
            if p[1] <= self.bounds[0]:
                self.addneighbour(positions, p)
            #south = 2
            p = [position[0], position[1]-1, 0, 0, self.straight, 2]
            if p[1] >= self.bounds[1]:
                self.addneighbour(positions, p)
            #east = 3
            p = [position[0]+1, position[1], 0, 0, self.straight, 3]
            if p[0] <= self.bounds[2]:
                self.addneighbour(positions, p)
            #west = 4
            p = [position[0]-1, position[1], 0, 0, self.straight, 4]
            if p[0] >= self.bounds[3]:
                self.addneighbour(positions, p)
        if freedom >= 8:
            #northeast = 5
            p = [position[0]+1, position[1]+1, 0, 0, self.diagonal, 5]
            if p[1] <= self.bounds[0] and p[0] <= self.bounds[2]:
                self.addneighbour(positions, p)
            #northwest = 6
            p = [position[0]-1, position[1]+1, 0, 0, self.diagonal, 6]
            if p[1] <= self.bounds[0] and p[0] >= self.bounds[3]:
                self.addneighbour(positions, p)
            #southeast = 7
            p = [position[0]+1, position[1]-1, 0, 0, self.diagonal, 7]
            if p[1] >= self.bounds[1] and p[0] <= self.bounds[2]:
                self.addneighbour(positions, p)
            #southwest = 8
            p = [position[0]-1, position[1]-1, 0, 0, self.diagonal, 8]
            if p[1] >= self.bounds[1] and p[0] >= self.bounds[3]:
                self.addneighbour(positions, p)
        return positions
    def letantsdance(self):
        if 0 < self.outrounds < self.rounds:
            mainloops = self.rounds/self.outrounds
            loops = self.outrounds
        else:
            mainloops = 1
            loops = self.rounds
        nrofrounds = mainloops*loops
        remember = loops
        while mainloops > 0:
            loops = remember
            while loops > 0:
                if len(self.ants) < self.maxants:
                    position = self.holes[randint(0, len(self.holes)-1)][0:2]
                    self.bear(None, self.antslife, position)
                for ant in self.ants:
                    ant.walk()
                self.volatilize()
                loops -= 1
            self.export(str(mainloops))
            print "nrofpaths:", self.nrop
            mainloops -= 1
        print "nrofrounds", nrofrounds
    def volatilize(self):
        if self.volatilizationtime > 0:
            limit = self.minpheromone
            halflife = self.volatilizationtime
            for x in range(self.bounds[2]):
                for y in range(self.bounds[0]):
                    if self.pherovapour[x][y] > limit:
                        val = int(self.pherovapour[x][y]*0.5**(1.0/halflife))
                        if val > limit:
                            self.pherovapour[x][y] = val
    def export(self, suffix=""):
        layer = self.playground.getlayer("phero")
        if self.outfilename == "":
            self.outfilename = layer.outfilename
        layer.setoutfilename(self.outfilename+suffix)
        layer.exportfile()

def test(inraster=False, outraster=False, invector=False, slope=False):
    """Test suite for ACO Class"""
    print "creating a new ants world.."
    w = ACO()
    if inraster:
        layer = w.importlayer("costs", "raster", inraster)
        w.costsurface = layer.raster
    elif slope:
        layer = w.importlayer("slope", "raster", slope)
        w.surfaceslope = layer.raster
        w.playground.setboundsfromlayer("slope")
        layer = w.createlayer("costs", "raster", None, None)
        w.costsurface = layer.raster
        w.calccostsurface()
    print "start playing with it.."
    if outraster and invector:
        layer = w.createlayer("phero", "raster", None, outraster)
        w.pherovapour = layer.raster
        layer = w.importlayer("holes", "vector", invector)
        w.holes = layer.objects
        w.rounds = 1
        w.checkvalues()
        print "set, within:", w.playground.getbounds()
        print "this translates to:", w.bounds
        print " this are the holes:"
        for hole in w.holes:
            print str(hole)
        print "neighbourpositions of [9,9]:", w.getneighbourpositions([9,9])
        print "setting [9,9] to pheromone 999"
        w.pherovapour[9][9] = 999
        w.volatilize()
        print " after some volatilization:",w.pherovapour[9][9]
        print "playing with some ants"
        w.letantsdance()
        print "rock n' roll"
        w.export()

