############################################################################
#
# MODULE:       r.agent.*
# AUTHOR(S):    michael lustenberger inofix.ch
# PURPOSE:      library file for the r.agent.* suite
# COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

import error
import agent
import playground

class World(object):
    """meta class"""
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
    def importlayer(self, name, typename=None, filename=None):
        if typename != None:
            self.playground.setlayerfromfile(name, typename, filename)
        elif filename != None:
            self.playground.getlayer(name).setinfilename(filename)
            self.playground.getlayer(name).importfile()
        else:
            self.playground.getlayer(name).importfile()
        return self.playground.getlayer(name)
    def createlayer(self, name, typename, infile=None, outfile=None):
        self.playground.setnewlayer(name, typename, False)
        if infile:
            self.playground.getlayer(name).setinfilename(infile)
        if outfile:
            self.playground.getlayer(name).setoutfilename(outfile)
        return self.playground.getlayer(name)
    def exportlayer(self, name, typename=None, filename=None):
        if filename == None:
            self.playground.getlayer(name).exportfile()
        elif typename == None:
            self.playground.getlayer(name).setoutfilename(filename)
        else:
            if not self.playground.getlayer(name):
                self.playground.setnewlayer(name, typename)
            self.playground.getlayer(name).setoutfilename(filename)
            self.playground.getlayer(name).exportfile()
    def setagenttype(self, agenttype):
        if issubclass(agenttype, self.agentclass):
            self.agenttype = agenttype
    def getagenttype(self):
        return self.agenttype
    def bear(self, agenttype=None, timetolife=0, position=[]):
        if agenttype == None:
            agenttype = self.agenttype
        if issubclass(agenttype, self.agentclass):
            self.agents.append(agenttype(timetolife, self, position))
    def moveto(self, agent, position):
        pass
    def move(self, agent, nrofsteps, direction="random"):
        pass
#        print "moving " + self.agent + self.nrofsteps + \
#            " steps towards " + self.direction
#    def letwalk(self, agent, nrofsteps=1, direction="random"):
#        position = agent.getposition()
#        npositions = self.playground.getneighbourpositions("costs", position)
        #agent.move()
    def kill(self, agent):
        self.agents.remove(agent)
#    def build(self, artefact):
#        self.artefacts.add(artefact)
#    def place(self, artefact, position):
#        pass
#    def destroy(self, artefact):
#        self.artefacts.remove(artefact)

def test(inraster=None, outraster=None, invector=None):
    """Test suite for World Class"""
    print "creating world"
    w = World()
    print "playing with agents"
    print " nothing changed.."
    print "  Agenttype is:", w.getagenttype()
    print " illegaly overwriting agent.."
    w.agenttype = ""
    print "  Agenttype is:", w.getagenttype()
    print " set new agenttype.."
    w.setagenttype(agent.Agent)
    print "  Agenttype is:", w.getagenttype()
    print "giving birth to some agents"
    w.bear()
    w.bear(agent.Agent)
    print " Agentlist:", w.agents
    print "killing an agent"
    w.kill(w.agents[0])
    print " Agentlist:", w.agents
#??    w.build()..
#??    w.moveto()..
#??    w.move()..
#??    w.place()..
#??    w.letwalk()..
#??    w.destroy()..
    print "adding layers?"
    if inraster:
        print "  adding raster"
        w.importlayer("raster", "raster", inraster)
        print "  re-adding again in diffrent way"
        w.createlayer("raster", "raster", inraster, inraster)
        w.importlayer("raster")
        print "  is set."
        if outraster:
            w.exportlayer("raster", "raster", outraster)
            print "  exported to:", str(outraster), "- check and remove.."
        if invector:
            print "  adding vectors"
            w.importlayer("vector", "vector", invector)
            print "  is set."

