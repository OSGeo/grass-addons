"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

import error, world, ant

#from grass.script import core as grass
from sys import maxsize
from math import sqrt
from math import exp
from random import randint

class Anthill(world.World):
    """
    World class for using the Ant Colony Optimization Algorithm for
    modelling Agent Based worlds.
    """
    # constant names for the layers
    SITE = "sitemap"
    COST = "penaltymap"
    RESULT = "pheromap"

    def __init__(self, pg=None):
        """
        Create a world based on the natural laws of the Ant Colony Optimization
        algorithm (plus adaptions honouring the complexity of the raster case).
        """
        # get all attributes from the basic world
        super(Anthill, self).__init__(pg, ant.Ant)
        # add the main layers
        ## one containing the points of interest
        self.addlayertopg(Anthill.SITE)
        ## one containing the time cost for traversing cells
        self.addlayertopg(Anthill.COST)
        ## allow overwriting the cost map
        self.overwritepenalty = False
        ## and finally the markings from the agents
        self.addlayertopg(Anthill.RESULT)
        ## allow overwriting the main map (if it exists)
        self.overwritepheormone = False
        # list of the points of origin / sites
        self.sites = []
        # default values
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

    def bear(self):
        """
        Set a new agent into the world
        @param int number of cycles the agent has to live
        @param list coordinates to put the agent on, none for a random position
        @return agent the newly created agent
        """
        position = self.sites[randint(0, len(self.sites)-1)]
        return super(Anthill, self).bear(self.antslife, position)

    def volatilize(self):
        """
        Let the pheromone evaporate over time.
        """
        self.playground.decaycellvalues(Anthill.RESULT, self.volatilizationtime,
                                            self.minpheromone)

    def letantsdance(self, rounds):
        """
        Let the agents do their job. The actual main loop in such a world.
        """
        while rounds > 0:
#            grass.info(rounds)
            if len(self.agents) < self.maxants:
#                grass.info(len(self.agents))
                # as there is still space on the pg, produce another ant
                self.bear()
            for ant in self.agents:
                # let all the ants take action
                ant.work()
            # let the pheromone evaporate
            self.volatilize()
            # count down
            rounds -= 1

