"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

import numpy, error, random

class Playground(object):
    """
    A Playground is a major component of a World, defining
    and organizing space.
    """

    def __init__(self):
        """Create a Playground"""
        self.layers = dict()
#TODO
        self.region = dict(n=1,s=0,w=0,e=1,rows=1,cols=1)

    def getregion(self):
        """
        Return the region information
        @return dict region
        """
        return self.region

    def getbound(self, bound):
        """
        Return the requested bound, takes: 'n', 's', 'w', or 'e'
        @param string bound
        @return float the outermost coordinate
        """
        if bound == "n" or bound == "s" or bound == "w" or bound == "e":
            return self.region[bound]

    def setlayer(self, layername, layer, force=False):
        """
        Put an existing map layer to the layer collection
        @param string name of the layer
        @param list a map layer
        @param boolean optional, whether to overwrite values if key exists
        """
        if not force and self.layers.has_key(layername):
            raise error.Error("r.agent::libagent.playground.Playground()",
                                    "May not overwrite existing layer.")
        self.layers[layername] = layer

    def createlayer(self, layername, filename=False, force=False):
        """
        Create a new layer and add it to the layer collection
        @param string name of the layer
        @param string optional name, whether to create it from an existing file
        @param boolean optional, whether to overwrite an existing layer
        """
        r = self.region["rows"]
        c = self.region["cols"]
        layer = numpy.zeros(r*c).reshape((r,c))

        if filename:
            #TODO import from file
            pass

        self.setlayer(layername, layer)

    def getlayer(self, layername):
        """
        Return a layer from the collection by its name
        @param string name of the layer
        @return list the requested map layer
        """
        retval = False
        if self.layers.has_key(layername):
            retval = self.layers[layername]
        return retval

    def removelayer(self, layername):
        """
        Remove (forget about) the layer named from the layer collection
        @param string name of the layer
        """
        if self.layers.has_key(layername):
            self.layers.pop(layername)

    def writelayer(self, layername, filename, force=False):
        """
        Write out a given layer to a certain file
        @param string name of the layer to be exported
        @param string name of the file to be written to
        @param boolean optional, whether an existing file may be overwritten
        """
        #TODO export to file
        #TODO overwrite policy: to increment or to fail?
        pass

    def getrandomposition(self):
        """
        Return a random position on the playground
        @return list some coordinates
        """
        ns = random.randrange(0,self.region["rows"])
        nw = random.randrange(0,self.region["cols"])
        return [ns,nw]
