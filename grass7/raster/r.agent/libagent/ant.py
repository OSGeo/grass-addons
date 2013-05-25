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
        self.position = [position[0], position[1], None, 0]
        self.home = self.position[:]
        self.laststeps = []
        self.visitedsteps = []
        self.nextstep = [None,None,None,0]
        self.goal = []
        self.penalty = 0.0
        self.walk = self.walkaround
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
        Check a list of positions for a position with a value of interest (<0)
        in the penalty layer, if such a position is really found, the ant
        happily turns back home by setting the next step to it's last.
        If it was only the homeposition, the removes it from the list and
        goes on.
        @param positions list of positions
        @return boolean whether such a position was found
        """
        for p in positions[:]:
            if self.world.getsitevalue(p) < 0:
                # this is what we are looking for!
                if p[0] == self.home[0] and p[1] == self.home[1]:
                    # ok, unfortunately we have only found the home position..
                    positions.remove(p)
                    # no other special should be so close to home, return..
                    return False
                else:
                    # goal node found!
                    self.world.numberofpaths += 1
                    #TODO for now just drop a line..
                    #self.world.playground.grassinfo("Found a path, total: " + \
                    #        str(self.world.numberofpaths))
                    # add one to the counter
                    #self.world.nrop += 1
                    self.walk = self.walkhome
                    # now, head back home..
                    self.nextstep = self.laststeps.pop()
                    return True
        return False

    def choose(self):
        """
        Make the decisions about where to go to next by first collecting
        all the possibilities (positions around), then looking whether
        a goal position is reached or else sorting out unwanted positions
        and finally choosing a next step by smell and random.
        """
        positions = self.world.getneighbourpositions(self.position)
        # check if we found a goal node, else pick a next step from the list
        if not self.evaluate(positions):
            self.nextstep = self.decide(positions)

    def walkhome(self):
        """
        Do all the things necessary for performing a regualar step when
        walking back home.
        """
        self.position = self.nextstep
        if len(self.laststeps) > 1:
            # walk only up to the gates of the hometown
            self.nextstep = self.laststeps.pop()
            self.penalty += self.nextstep[3] + \
                              self.world.getpenalty(self.nextstep)
        else:
            # retire after work.
            self.snuffit()
        self.world.setpathpheromone(self.position)

    def walkaround(self):
        """
        Do all the things necessary for performing a regualar step when
        walking around.
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
            # exit if we died in the meantime..
            return False
        # past this point we must have decided yet where to go to next..
        if self.nextstep[0] == None:
            # so we'll have to decide it now if it was not clear yet
            self.choose()
            self.penalty += self.nextstep[3] + \
                                self.world.getpenalty(self.nextstep)
        # if penalty is positive, wait one round
        if self.penalty > 0:
            self.penalty -= 1
            return True
        else:
            self.walk()

