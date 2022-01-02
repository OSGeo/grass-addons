"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2015 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

from random import uniform

from libagent import agent

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range


class Ant(agent.Agent):
    """
    Implementation of an Ant like Agent for an Anthill, a kind of World
    that works after ACO rules (see Anthill).

    Ants are wandering around by chance until they find some goal cell,
    then they will mark their way back home with pheromone. Following ants
    choose the marked cells on the playground more likely than unmarked
    spots.

    There are several optimizations / idealizations to choose from,
    as ACO comes from graph theory and raster layers map quite large
    graphs (e.g. loops are a major source of sorrow).
    """

    def __init__(self, timetolive, world, position):
        """
        Create an Agent for an Anthill World
        @param int time to live
        @param World the agent knows the worlds he lives in
        @param list coordinate of the current position
        """
        super(Ant, self).__init__(timetolive, world, position)
        # position layout: [x][y][orientation][penalty]
        # orientation (to the last position):
        # south (=0) north (=1) east (=3) south-west (=4)
        # north-west (=5) south-east (=6) north-east (=7)
        # penalty: 1 straight, sqr(2) diagonal
        self.position = [position[0], position[1], None, 0]
        self.home = self.position[:]
        self.laststeps = []
        self.visitedsteps = []
        self.nextstep = [None, None, None, 0]
        self.goal = []
        self.penalty = 0.0
        self.walk = self.walkaround
        if self.world.decisionbase == "random":
            # TODO: for now like 'else'..
            self.decide = self.randomposition
        if self.world.decisionbase == "marked":
            self.decide = self.markedposition
        if self.world.decisionbase == "costlymarked":
            self.decide = self.costlymarkedposition
        else:
            # standard is marked for the moment..
            self.decide = self.markedposition
        if self.world.evaluationbase == "standard":
            self.evaluate = self.check
        else:
            self.evaluate = self.check

    def check(self, positions):
        """
        Evaluate a list of positions for a position with a value of interest
        (<0) in the penalty layer, if such a position really is found, the ant
        happily turns back home by setting the next step to it's last.
        If it was only the homeposition, the ant removes it from the list and
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
                    # TODO for now just drop a line..
                    # self.world.playground.grassinfo("Found a path, total: " + \
                    #        str(self.world.numberofpaths))
                    # add one to the counter
                    # self.world.nrop += 1
                    self.walk = self.walkhome
                    # now, head back home..
                    self.nextstep = self.laststeps.pop()
                    return True
        return False

    def costlymarkedposition(self, positions):
        """
        Avoiding high values on the costsurface, combined with the
        marked pheromone values on a certain layer combined with a random
        value, pick a position out of a list of positions.
        @param positions list of possible positions
        @return position the decision for a position
        """
        # sort out illegal positions
        copyofpositions = positions[:]
        for i in xrange(0, len(positions)):
            p = copyofpositions[i]
            penalty = self.world.getpenalty(p)
            if (penalty < self.world.minpenalty) or (penalty > self.world.maxpenalty):
                positions.remove(p)
        if not positions:
            # die as there is nowhere to go to
            self.snuffit()
            # make sure to not walk again..
            return [0, 0, 99, 99]

        position = positions[0]
        # compare the remaining
        tmpval = (
            -self.world.getpenalty(position) * self.world.costweight
            + self.world.getpheromone(position) * self.world.pheroweight
            + uniform(self.world.minrandom, self.world.maxrandom)
            * self.world.randomweight
        )
        for i in xrange(1, len(positions)):
            p = positions[i]
            newval = (
                -self.world.getpenalty(p) * self.world.costweight
                + self.world.getpheromone(p) * self.world.pheroweight
                + uniform(self.world.minrandom, self.world.maxrandom)
                * self.world.randomweight
            )
            if newval > tmpval:
                position = p
                tmpval = newval
        return position

    def markedposition(self, positions):
        """
        Based on the value on a certain layer combined with a random
        value, pick a position out of a list of positions.
        @param positions list of possible positions
        @return position the decision for a position
        """
        position = positions[0]
        tmpval = (
            self.world.getpheromone(position) * self.world.pheroweight
            + uniform(self.world.minrandom, self.world.maxrandom)
            * self.world.randomweight
        )
        for i in xrange(1, len(positions)):
            p = positions[i]
            newval = (
                self.world.getpheromone(p) * self.world.pheroweight
                + uniform(self.world.minrandom, self.world.maxrandom)
                * self.world.randomweight
            )
            if newval > tmpval:
                position = p
                tmpval = newval
        return position

    def choose(self):
        """
        Make the decisions about where to go to next by first collecting
        all the possibilities (positions around), then looking whether
        a goal position is reached or else sorting out unwanted positions
        and finally choosing a next step by smell and/or random.
        """
        positions = self.world.getneighbourpositions(self.position)
        # check if we found a goal node, else pick a next step from the list
        if not self.evaluate(positions):
            self.nextstep = self.decide(positions)

    def walkhome(self):
        """
        Do all the things necessary for performing a regular step when
        walking back home.
        """
        self.position = self.nextstep
        if len(self.laststeps) > 1:
            # try to avoid loops
            if self.world.antavoidsloops:
                # Find the first occurence of this step in the path array
                i = self.laststeps.index(self.laststeps[-1])
                # Forget the path (the loop) inbetween
                self.laststeps = self.laststeps[0 : i + 1]
            # walk only up to the gates of the hometown
            self.nextstep = self.laststeps.pop()
            self.penalty += self.nextstep[3] + self.world.getpenalty(self.nextstep)
        else:
            # retire after work.
            self.snuffit()
        self.world.setpathpheromone(self.position)

    def walkaround(self):
        """
        Do all the things necessary for performing a regular step when
        walking around.
        """
        self.laststeps.append(self.position)
        self.position = self.nextstep
        self.nextstep = [None, None, None, 0]
        self.world.setsteppheromone(self.position)

    def work(self):
        """
        Wander around searching for fields of interest, mark the
        road back home.
        @return boolean whether still alive
        """
        # we are all only getting older..
        if not self.age():
            # exit if we died in the meantime..
            return False
        # at this point either we already know where to go to next..
        if self.nextstep[0] is None:
            # ..or we'll have to decide it now if it was not clear yet
            self.choose()
            self.penalty += self.nextstep[3] + self.world.getpenalty(self.nextstep)
        # if penalty is positive, wait one round
        if self.penalty > 0:
            self.penalty -= 1
            return True
        else:
            self.walk()
