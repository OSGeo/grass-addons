"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2015 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

from random import randint
from sys import maxsize

from libagent import ant, world


class Anthill(world.World):
    """
    This kind of world makes use of the Ant Colony Optimization (ACO)
    algorithm for coordinating its agent's actions (for ACO, see
    https://en.wikipedia.org/wiki/Ant_colony_optimization_algorithms).

    The agents are implemented as ants, wandering around by chance
    if they find a goal cell they will mark their way back home
    with pheromone. The following ants then choose the marked cells
    on the playground more likely than unmarked spots. The pheromone
    evaporates over time.
    """

    # constant names for the layers
    SITE = "sitemap"
    COST = "penaltymap"
    RESULT = "pheromap"

    def __init__(self, pg=None):
        """
        Create a world based on the natural laws of the ACO algorithm
        (plus adaptions honouring the complexity of the raster case).
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
        # TODO probably delete all these stuff here related to output..
        self.addsequencenumber = False
        ## and finally the markings from the agents
        self.addlayertopg(Anthill.RESULT)
        ## allow overwriting the main map (if it exists)
        self.overwritepheormone = False
        # list of the points of origin / sites
        self.sites = []
        # default values
        ## let ant die if penalty grows too big
        self.maxpenalty = 99999
        self.minpenalty = 0
        ## max/min possible value of pheromone intensity
        self.maxpheromone = maxsize
        self.minpheromone = 0
        ## max/min value for random values
        self.maxrandom = self.maxpheromone
        self.minrandom = self.minpheromone
        ## half value period for pheromone
        self.volatilizationtime = 8
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
        self.maxants = self.playground.gettotalcount()
        ## the ants ttl will be set by user or based on playground size
        self.antslife = 2 * self.playground.getdiagonalcount()
        self.antavoidsloops = False
        self.decisionbase = "standard"
        self.evaluationbase = "standard"
        self.numberofpaths = 0

    def bear(self):
        """
        Set a new agent into the world
        @param int number of cycles the agent has to live
        @param list coordinates to put the agent on, none for a random position
        @return agent the newly created agent
        """
        position = self.sites[randint(0, len(self.sites) - 1)]
        return super(Anthill, self).bear(self.antslife, position)

    def volatilize(self):
        """
        Let the pheromone evaporate over time.
        """
        self.playground.decaycellvalues(
            Anthill.RESULT, self.volatilizationtime, self.minpheromone
        )

    def letantsdance(self, rounds):
        """
        Let the agents do their job. The actual main loop in such a world.
        """
        while rounds > 0:
            #            grass.info(len(self.agents))
            if len(self.agents) <= self.maxants:
                # as there is still space on the pg, produce another ant
                self.bear()
            for ant in self.agents:
                # let all the ants take action
                ant.work()
            # let the pheromone evaporate
            self.volatilize()
            # count down
            rounds -= 1

    def getpheromone(self, position):
        """
        Return the pheromone value at a certain position
        @param position the position in question
        @return the value of interest
        """
        return self.playground.getcellvalue(Anthill.RESULT, position)

    def setpheromone(self, position, intensity=None):
        """
        Mark a certain position with pheromone
        @param position the position in question
        @param intensity the value to be set
        """
        self.playground.setcellvalue(Anthill.RESULT, position, intensity)

    def setsteppheromone(self, position):
        """
        Mark a certain position with the pheromone of step intensity
        @param position the position in question
        """
        intensity = self.getpheromone(position) + self.stepintensity
        if intensity < self.maxpheromone:
            self.setpheromone(position, intensity)
        else:
            self.setpheromone(position, self.maxpheromone)

    def setpathpheromone(self, position):
        """
        Mark a certain position with the pheromone of path intensity
        @param position the position in question
        """
        intensity = self.getpheromone(position) + self.pathintensity
        if intensity < self.maxpheromone:
            self.setpheromone(position, intensity)
        else:
            self.setpheromone(position, self.maxpheromone)

    def getpenalty(self, position):
        """
        Return the penalty value at a certain position
        @param position the position in question
        @return the value of interest
        """
        return self.playground.getcellvalue(Anthill.COST, position)

    def getsitevalue(self, position):
        """
        Return the value at a certain position in the sites layer
        @param position the position in question
        @return the value of interest
        """
        return self.playground.getcellvalue(Anthill.SITE, position)
