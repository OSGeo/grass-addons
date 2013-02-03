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
    """World class for using the Ant Colony Optimization Algorithm for
       modelling Agent Based worlds."""
    def __init__(self):
        # get all attributes from the basic world
        super(ACO, self).__init__(ant.Ant)
        # add the main layers
        ## one containing the points of interest
        self.addlayertopg("sitemap")
        ## one containing the time cost for traversing cells
        self.addlayertopg("penaltymap")
        ## and finally the markings from the agents
        self.addlayertopg("pheromap")
        # list of the points of origin / sites
        self.holes = []

