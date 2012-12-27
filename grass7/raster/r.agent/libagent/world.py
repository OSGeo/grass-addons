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
import playground
import agent

class World(object):
    """Generic World class as basis for more complex worlds."""
    def __init__(self, agenttype=None, pg=None):
        if pg == None:
            self.playground = playground.Playground()
        else:
            self.playground = pg
        self.agentclass = agent.Agent
        if agenttype == None:
            self.agenttype = self.agentclass
        else:
            self.setagenttype(agenttype)
        self.agents = []
        self.artefacts = []
    def addlayertopg(self, layername, layertype):
        pass
    def getlayer(self, layername):
        pass
#       return layer
    def rmlayer(self, layername):
        pass
    def setagenttype(self, agentype):
        pass
    def getagenttype(self):
        pass
#       return agenttype
    def bear(self, timetolive, position, agenttype):
        pass
#       return agent
    def getnextagent():
        return next(self, agents)
    def move(self, agent, position):
        pass
    def getposition(self, agent):
        pass
    def kill(self, agent):
        pass

