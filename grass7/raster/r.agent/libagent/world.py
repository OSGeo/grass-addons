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

    def __init__(self, agenttype=None, pg=None, freedom=8):
        """
        Create a World, a place with a playground, where agents meet
        @param type optional, the default agent type for this world
        @param playground optional, if playground already exists
        """
        if pg == None:
            self.playground = playground.Playground()
        else:
            self.playground = pg
        if agenttype == None:
            self.agenttype = agent.Agent
        else:
            self.agenttype = agenttype
        self.agents = []
        #self.artefacts = []
        self.freedom = freedom

    def addlayertopg(self, layername):
        """
        Add a new layer to the playground
        @param string name for the new layer
        """
        self.playground.createlayer(layername)

    def removelayerfrompg(self, layername):
        """
        Remove the named layer from the playground
        @param string name of the layer to be removed
        """
        self.playground.removelayer(layername)

    def getlayer(self, layername):
        """
        Access a layer by its name
        @param string name of the layer
        @return the layer
        """
        return self.playground.getlayer(layername)

    def bear(self, timetolive, position=None, agenttype=None):
        """
        Set a new agent into the world
        @param int number of cycles the agent has to live
        @param list coordinates to put the agent or none for a random position
        @return agent the newly created agent
        """
        if not position:
            position = self.playground.getrandomposition()
        agent = self.agenttype(timetolive, self, position)
        self.agents.append(agent)
        return agent

    def move(self, agent, position):
        """
        Set agent to a new position
        @param agent to be moved
        @param list coordinates of the new position
        """
        pass

    def getposition(self, agent):
        """
        Ask the agent for its current position
        @param agent to be asked
        """
        pass

    def getneighbourpositions(self, position, freedom=None):
        """
        Get all the positions reachable
        @param list coordinates of a certain cell
        @param int number of potentially reachable neighbours
        @return list list of coordinates
        """
        if not freedom:
            freedom = self.freedom
        pass
        #return

    def kill(self, agent):
        """
        Remove the agent from the list
        @param agent to be terminated
        """
        pass

