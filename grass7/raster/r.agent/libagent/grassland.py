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
from grass.script import array as garray

class GrassLand(playground.Playground):
    """A GrassLand is a Playground and the interface to GRASS."""
    def __init__(self):
        """Create a Playground with all the relevant info by GRASS"""
        self.layers = dict()
        self.grassmapnames = dict()
        self.region = grass.region()
        if self.region['ewres'] != self.region['nsres']:
            raise error.DataError("r.agent::libagent.playground.Playground()",
                                    "Only square raster cells make sense.")
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
                                    "May not overwrite existing layer."))
        self.layers[layername] = layer
    def setgrasslayer(self, layername, grassmapname, force=False):
        """
        Put an existing map from GRASS to the layer collection
        @param string name of the layer
        @param string name of a GRASS map layer
        @param boolean optional, whether to overwrite values if key exists
        """
        layer = garray.array()
        if grassmapname:
            # fill the new grass array with the contents from the file
            layer.read(grassmapname)
            self.grassmapnames[layername] = grassmapname
        self.setlayer(layername, layer, force)
    def createlayer(self, layername, force=False):
        """
        Create a new layer and add it to the layer collection
        @param string name of the layer
        @param string name of a GRASS map layer or False if layer is only local
        """
        self.setgrasslayer(layername, False, force)
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
#    def writelayer(self, layername):
#        pass

