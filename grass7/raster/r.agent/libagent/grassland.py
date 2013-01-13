"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

import grass.script as grass

class GrassLand(playground.Playground):
    """A GrassLand is a Playground and the interface to GRASS."""
    def __init__(self):
        """Create a Playground with all the relevant info by GRASS"""
        self.layers = dict()
        self.region = grass.region()
        if self.region['ewres'] != self.region['nsres']:
            raise error.DataError("r.agent::libagent.playground.Playground()",
                                    "Only square raster cells make sense.")
    def getregion(self):
        """Return the region information"""
        return self.region
    def getbound(self, bound):
        """Return the requested boundary, takes: 'n', 's', 'w', or 'e'"""
        if bound == "n" or bound == "s" or bound == "w" or bound == "e":
            return self.region[bound]
    def setlayer(self, layername, layer, force=False):
        """Put an existing map from GRASS to the layer collection"""
        pass
    def createlayer(self, layername, grassmap=False):
        """Create a new layer and add it to the layer collection"""
        pass
    def getlayer(self, layername):
        """Return a layer from the collection by its name"""
        return []
    def removelayer(self, layername):
        """Remove the layer named from the layer collection"""
        pass
#    def writelayer(self, layername):
#        pass

