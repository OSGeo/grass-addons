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

import world

class Agent(object):
    """standard agent"""
    def __init__(self, timetolive, world, position=[]):
        self.ttl = timetolive
        self.world = world
        self.position = position
        self.knowscompass = False
        self.freedom = 0
    def setposition(self, position):
        if position and position != []:
            self.position[0] = position[0]
            self.position[1] = position[1]
    def getposition(self):
        return self.position
    def move(self, nrofsteps, direction):
        pass
    def age(self):
        if self.ttl > 0:
            self.ttl -= 1
            return True
        else:
            self.snuffit()
            return False
    def snuffit(self):
        """to die peacefully and without pain."""
        self.world.kill(self)

def test():
    """Test suite for Agent Class"""
    print "create a world with an agent in."
    w = world.World(Agent)
    w.bear(Agent,1,[0,0])
    print "agent seems fine (for now). time to live:", str(w.agents[0].ttl)
    print "fake-placing it somewhere ([0,1]).."
    w.agents[0].setposition([0,1])
    print "getting its position:", w.agents[0].getposition()
    print "'cause this takes some time.."
    w.agents[0].age()
    print "agent should have grown older by now. time to live:", \
         str(w.agents[0].ttl)
    print "and now let agent die.."
    w.agents[0].age()
    try:
        print "should be dead by now. time to live:", str(w.agents[0].ttl)
    except IndexError:
        print "IndexError catched: ant was not found in the world anymore."
    print "all done."

