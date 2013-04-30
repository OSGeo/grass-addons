"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

from random import choice, randint
import agent
import error

class Ant(agent.Agent):
    """Implementation of an Ant Agent for an Anthill, an ACO kind of World."""

    def __init__(self, timetolive, world, position):
        """
        Create an Agent for an Anthill World
        @param int time to live
        @param World the agent knows the worlds he lives in
        @param list coordinate of the current position
        """
        super(Ant, self).__init__(timetolive, world, position)
        self.position.extend([None,None,0,0])
        self.home = self.position[:]
        self.laststeps = [self.position[:]]
        self.visitedsteps = []
        self.done = False
        self.nextstep = [None,None,0,0,0,0]
        self.goal = []
        self.penalty = 0.0

    def walk(self):
        pass

