"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

import error
import world
import ant

from sys import maxsize
from math import sqrt
from math import exp
from random import randint

class ACO(world.World):
    """
    World class for using the Ant Colony Optimization Algorithm for
    modelling Agent Based worlds.
    """
    # constant names for the layers
    SITE = "sitemap"
    COST = "penaltymap"
    RESULT = "pheromap"

    def __init__(self):
        """
        Create a world based on the natural laws of the Ant Colony Optimization
        algorithm (plus adaptions honouring the complexity of the raster case).
        """
        # get all attributes from the basic world
        super(ACO, self).__init__(ant.Ant)
        # add the main layers
        ## one containing the points of interest
        self.addlayertopg(ACO.SITE)
        ## one containing the time cost for traversing cells
        self.addlayertopg(ACO.COST)
        ## allow overwriting the cost map
        self.overwritepenalty = False
        ## and finally the markings from the agents
        self.addlayertopg(ACO.RESULT)
        ## allow overwriting the main map (if it exists)
        self.overwritepheormone = False
        # list of the points of origin / sites
        self.sites = []
        # default values
        ## how many rounds to go
        self.rounds = 0
        ## when to produce output
        self.outrounds = 0
        ## let ant die if penalty grows too big
        self.maxpenalty = 0
        ## max/min possible value of pheromone intensity
        self.maxpheromone = maxsize
        self.minpheromone = 10
        ## half value period for pheromone
        self.volatilizationtime = 1
        ## ants mark every step with this pheromone value
        self.stepintensity = 10
        ## ants mark every found path with this pheromone intensity
        self.pathintensity = 10000
        ## penalty values above this point an ant considers as illegal
        self.highcostlimit = 0
        ## penalty values below this point an ant considers as illegal
        self.lowcostlimit = 0
        ## how to weigh the values found on the playground
        self.pheroweight = 1
        self.randomweight = 1
        self.costweight = 1
        ## maximum number of ants on the playground
        self.maxants = 100
        ## the ants ttl will be set by user or based on playground size
        self.antslife = 0
#TODO        self.decisionbase = "default"
#TODO        self.rememberbase = "default"

    def letantsdance(self):
        """
        Organize the agents and the pheromone on the playground.
        """
        if 0 < self.outrounds < self.rounds:
            # calculate when to write output
            mainloops = self.rounds / self.outrounds
            nextwrite = self.outrounds
        else:
            # produce output only at the end
            mainloops = 1
            nextwrite = self.rounds
        while mainloops > 0:
            # loop and write out the contents at the end
            loops = nextwrite
            while loops > 0:
                # loop without producing output
                if len(self.agents) < self.maxants:
                    # as there is still space on the pg, produce another ant
                    # at a random site..
                    position = self.sites[randint(0, len(self.sites)-1)]
                    self.bear(self.antslife, position)
                for ant in self.agents:
                    # let all the ants take action
                    ant.walk()
                # let the pheromone evaporate
                self.volatilize()
                # count down inner
                loops -= 1
            # export the value maps
            self.writeout()
#            print "nrofpaths:", self.nrop
            # count down outer
            mainloops -= 1
#        print "nrofrounds", nrofrounds

    def volatilize(self):
        """
        Let the pheromone evaporate over time.
        """
        self.playground.decaycellvalues(ACO.RESULT, self.volatilizationtime,
                                            self.minpheromone)

    def writeout(self):
        """
        Write the results back onto the maps.
        """
        pass

