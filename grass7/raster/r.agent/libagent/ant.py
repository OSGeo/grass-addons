"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

from random import choice #, randint
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
        self.position.extend([None,None])
        self.home = self.position[:]
        self.laststeps = [self.position[:]]
        self.visitedsteps = []
        self.done = False
        self.nextstep = [None,None,None,0]
        self.goal = []
        self.penalty = 0.0
        if self.world.decisionbase == "standard":
            # TODO: for now like 'else'..
            self.decide = self.randomposition
        else:
            self.decide = self.randomposition
        if self.world.evaluationbase == "standard":
            self.evaluate = self.check
        else:
            self.evaluate = self.check

    def check(self, positions):
        """
        """
        for p in positions[:]:
            if self.world.getpenalty(p) < 0:
                # this is what we are looking for!
                if p[0] == self.home[0] and p[1] == self.home[1]:
                    # ok, unfortunately we have only found the home position..
                    positions.remove(p)
                    # no other special should be so close to home, return..
                    return False
                else:
                    # goal node found!
                    # add one to the counter
                    #self.world.nrop += 1
                    self.done = True
                    # now, head back home..
                    self.nextstep = self.laststeps.pop()
                    return True
        return False

    def choose(self):
        """
        """
        positions = self.world.getneighbourpositions(self.position)
        if not self.evaluate(positions):
            self.nextstep = self.decide(positions)

    def walk(self):
        """
        """
        self.laststeps.append(self.position)
        self.position = self.nextstep
        self.nextstep = [None,None,None,0]
        self.world.setsteppheromone(self.position)

    def work(self):
        """
        Wander around searching for fields of interest, mark the
        road back home.
        @return boolean whether still alive
        """
        # we are all only getting older..
        if self.age() == False:
            return False
        # past this point we must have decided yet where to go to next..
        if self.nextstep[0] == None:
            self.choose()
            self.penalty += self.nextstep[3] + \
                                self.world.getpenalty(self.nextstep)
        # if penalty is positive, wait one round
        if self.penalty > 0:
            self.penalty -= 1
            return True
        else:
            self.walk()

