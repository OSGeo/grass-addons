"""
MODULE:       r.agent.* aco
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      the controller part for r.agent.aco of the r.agent.* suite or
              similar.
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

from libagent import error, grassland, anthill

from sys import maxsize
from math import sqrt
from math import exp
from random import randint

# initialize the number of iterations
rounds = 0
outrounds = 0

# take out a subscription for a playground to a world
world = anthill.Anthill(grassland.Grassland())

def setmaps(site, cost, wastecosts, inphero, outphero, wastephero):
    """
    Set the user maps in place
    """
    if site:
        # set sitemap and site list
        world.sites = world.playground.parsevectorlayer(anthill.Anthill.SITE,
                                                        site, True)
    else:
        raise error.DataError("aco:", "The site map is mandatory.")
    if cost:
        # set cost/penalty layer
        world.playground.setgrasslayer(anthill.Anthill.COST, cost, True)
        world.overwritepenalty = wastecosts
    if inphero == outphero:
        if not wastephero:
            raise error.DataError("aco:", "May not overwrite the output map.")
    if inphero:
        world.playground.setgrasslayer(anthill.Anthill.RESULT, inphero, True)
    world.playground.grassmapnames[anthill.Anthill.RESULT] = outphero
    world.overwritepheormone = wastephero

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
#        print "nrofpaths:", self.nrop
        # count down outer
        mainloops -= 1
#    print "nrofrounds", nrofrounds

