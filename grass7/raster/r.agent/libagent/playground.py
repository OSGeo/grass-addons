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

class Playground(object):
    """A Playground is a major component of a World, defining
       and organizing space, and the interface to GRASS."""
    def __init__(self):
        self.layers = dict()
        self.region = grass.region()
        if self.region['ewres'] != self.region['nsres']:
            raise error.DataError("r.agent::libagent.playground.Playground()",
                                    "Only square raster cells make sense.")
    def getregion(self):
        return self.region
    def getbound(self, bound):
        return self.region[bound]
    def setlayer(self, layername, layer, force=False):
        pass
    def createlayer(self, layername, grassmap=False):
        pass
    def getlayer(self, layername):
        return []
    def removelayer(self, layername):
        pass
    def writelayer(self, layername):
        pass

